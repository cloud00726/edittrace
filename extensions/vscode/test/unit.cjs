'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {invoke, withInput} = require('../bridge');
const path = require('node:path');
const fs = require('node:fs');
const vm = require('node:vm');
test('transport rejects absent executable', async () => {
  await assert.rejects(invoke(path.resolve('not an executable'), []));
  await assert.rejects(invoke('relative-path', []), /absolute/);
});
test('cancellation, timeout and output failures remain errors', async () => {
  const controller = new AbortController(); controller.abort();
  await assert.rejects(invoke(process.execPath, ['-e','setInterval(()=>{},1000)'], {signal: controller.signal}), /canceled/);
  await assert.rejects(invoke(process.execPath, ['-e','setInterval(()=>{},1000)'], {timeout: 100}), /timed out/);
  await assert.rejects(invoke(process.execPath, ['-e','console.log("invalid-json")']), /invalid JSON/);
  await assert.rejects(invoke(process.execPath, ['-e','process.exit(2)']), /exit 2/);
});
test('argument arrays preserve spaces and shell characters without execution', async () => {
  const value='spaces & $(ignored) `literal`';
  const result=await invoke(process.execPath, ['-e','console.log(JSON.stringify({exit_code:0,value:process.argv[1]}))',value]);
  assert.equal(result.report.value,value);
});
test('process and report status must agree', async () => {
  await assert.rejects(invoke(process.execPath, ['-e','console.log(JSON.stringify({exit_code:1}))']), /disagree/);
});
const root = path.resolve(__dirname, '../../..');
const core = ['edittrace.exe','edittrace'].map(n => path.join(root,'_build/native/debug/build/cmd/edittrace',n)).find(p => fs.existsSync(p));
test('captured host tie-order regression replays through the real core (mocked host only)', {skip: !core}, async () => {
  const captured=JSON.parse(fs.readFileSync(path.join(root,'examples/real-world/same-position-events.case.json'),'utf8'));
  const records=captured.input.records;
  const opened=records.find(r=>r.message?.method==='textDocument/didOpen').message.params.textDocument;
  const event=records.find(r=>r.message?.method==='textDocument/didChange').message.params;
  const actual=records.find(r=>r.kind==='checkpoint');
  const extension={exports:{}};
  const host={version:'captured-regression-mock'};
  vm.runInNewContext(fs.readFileSync(path.join(root,'extensions/vscode/extension.js'),'utf8'), {module:extension,exports:extension.exports,require:name=>name==='vscode'?host:name==='./bridge'?require('../bridge'):require(name),Buffer,AbortController});
  const recorder=new extension.exports.Recorder();
  recorder.append(records[0]);
  const doc={uri:{scheme:'file',toString:()=>opened.uri},languageId:opened.languageId,version:opened.version,getText:()=>opened.text};
  recorder.open(doc);
  doc.version=event.textDocument.version;doc.getText=()=>actual.text;
  recorder.changed({document:doc,contentChanges:event.contentChanges.map(c=>({range:c.range,text:c.text,rangeOffset:1,rangeLength:0}))});
  assert.equal((await withInput(core,'audit',recorder.stop())).code,0);
});

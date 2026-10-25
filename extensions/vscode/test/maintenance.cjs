'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');
const vm = require('node:vm');
const project = require('../project');
const {diagnose,providerCall,checkCapabilities} = require('../diagnostics');
const {reportText,diffChoices} = require('../presentation');
const {withInput} = require('../bridge');
const root=path.resolve(__dirname,'../../..');
const fixture=()=>require(path.join(root,'examples/real-world/format.case.json'));
const core=['edittrace.exe','edittrace'].map(n=>path.join(root,'_build/native/debug/build/cmd/edittrace',n)).find(p=>require('node:fs').existsSync(p));
async function workspace(fn) {const p=await fs.mkdtemp(path.join(os.tmpdir(),'edittrace-regression-test-'));try{return await fn(p);}finally{await fs.rm(p,{recursive:true,force:true});}}

test('provider errors, empty return evidence and timeout are distinct',async()=>{
  await assert.rejects(providerCall(()=>{throw new Error('provider unavailable');}),/Provider failed/);
  await assert.rejects(providerCall(()=>new Promise(()=>{}),15),/Provider timed out/);
  assert.deepEqual(await providerCall(()=>[]),[]);
});
test('real core doctor verifies protocol capabilities and missing core is actionable',async()=>{
  const r=await diagnose(core,{platform:process.platform,host_version:'test-host'});
  assert.equal(r.compatible,true);assert.equal(r.bridge_protocol,1);
  await assert.rejects(diagnose(path.join(root,'missing-core'),{}),/not found/);
  assert.throws(()=>checkCapabilities({...r,bridge_protocol:2}),/Incompatible/);
  assert.doesNotThrow(()=>checkCapabilities({...r,core_version:'future-compatible-core'}));
});
test('summaries reject malformed reports and render controls without executing markup',()=>{
  assert.throws(()=>reportText({exit_code:0}),/status/);
  assert.throws(()=>reportText({exit_code:0,analysis_complete:true}),/summary/);
  const rendered=reportText({exit_code:2,analysis_complete:false,display_summary:'INCOMPLETE\n\x1b[31m<script>\u202e'});
  assert.ok(rendered.includes('INCOMPLETE\n'));assert.ok(!rendered.includes('\x1b'));assert.ok(rendered.includes('\\u202e'));
});
test('every file is selectable and actual evidence is validated',()=>{
  const docs=[{uri:'file:///a',text:'A',actual_compared:false},{uri:'file:///b',text:'B',actual_compared:true,actual_text:'B'}];
  const last={kind:'edit_plan',plan:{documents:[{uri:'file:///a',text:'a'},{uri:'file:///b',text:'b'}]},report:{documents:docs}};
  assert.equal(diffChoices(last).length,2);assert.equal(diffChoices(last)[1].document.actual_text,'B');
  delete docs[1].actual_text;assert.throws(()=>diffChoices(last),/actual/);
});
test('draft, review, content changes, failure detection and migration use real core',async()=>workspace(async p=>{
  const saved=await project.save(p,fixture());
  await assert.rejects(project.suite(p),/No unchanged confirmed/);
  const [draft]=await project.discover(p);assert.equal(draft.status,'draft');
  await assert.rejects(project.confirm(p,'../escape.json',draft.sha256),/Invalid/);
  await project.confirm(p,saved.name,draft.sha256);
  const suite=await project.suite(p);
  assert.equal((await withInput(core,['suite','run'],suite.value)).code,0);
  const changed=structuredClone(draft.value);changed.expect.texts[0].text='intentional wrong expectation';
  await fs.writeFile(saved.file,JSON.stringify(changed));
  assert.equal((await project.discover(p))[0].status,'changed');
  await assert.rejects(project.suite(p),/No unchanged confirmed/);
  await assert.rejects(project.confirm(p,saved.name,draft.sha256),/changed during review/);
  assert.equal((await withInput(core,['case','run'],changed)).code,1);
  // Restore bytes only through explicit fixture rewrite, then review that exact content again.
  await fs.writeFile(saved.file,JSON.stringify(draft.value));
  const restored=(await project.discover(p))[0];await project.confirm(p,saved.name,restored.sha256);
  const migrated=path.join(p,'migrated');await fs.mkdir(migrated);await fs.cp(path.join(p,'.edittrace'),path.join(migrated,'.edittrace'),{recursive:true});
  assert.equal((await withInput(core,['suite','run'],(await project.suite(migrated)).value)).code,0);
}));
test('malformed metadata and symlink files cannot become confirmed regressions',async()=>workspace(async p=>{
  const saved=await project.save(p,fixture());
  await fs.writeFile(saved.file+'.review.json','{"status":"confirmed"}');
  assert.equal((await project.discover(p))[0].status,'invalid');
  await assert.rejects(project.suite(p),/Invalid regression/);
  await assert.rejects(project.confirm(p,saved.name,'wrong'),/changed during review/);
  // Directory junctions can be created on Windows without symlink privileges.
  const alternate=path.join(p,'other');await fs.mkdir(alternate);
  const linked=path.join(p,'linked');await fs.mkdir(linked);
  await fs.symlink(alternate,path.join(linked,'.edittrace'),process.platform==='win32'?'junction':'dir');
  await assert.rejects(project.init(linked),/not a link/);
}));
test('independent roots and existing project files remain isolated',async()=>workspace(async p=>{
  const a=path.join(p,'a'),b=path.join(p,'b');await fs.mkdir(a);await fs.mkdir(b);
  await project.save(a,fixture());await project.init(b);
  assert.equal((await project.discover(a)).length,1);assert.equal((await project.discover(b)).length,0);
  const readme=path.join(b,'.edittrace','README.md');await fs.writeFile(readme,'user text');await project.init(b);assert.equal(await fs.readFile(readme,'utf8'),'user text');
}));
test('multi-root selection and cancellation use only the chosen local folder',async()=>{
  const commands=new Map();let pick;
  const host={version:'mock-root-selection',commands:{registerCommand:(name,fn)=>{commands.set(name,fn);return{dispose(){}};}},workspace:{workspaceFolders:[{name:'a',uri:{scheme:'file',fsPath:'/a'}},{name:'b',uri:{scheme:'file',fsPath:'/b'}}]},window:{showQuickPick:async items=>pick===undefined?undefined:items[pick]}};
  const extension={exports:{}};
  vm.runInNewContext(require('node:fs').readFileSync(path.join(root,'extensions/vscode/extension.js'),'utf8'),{module:extension,exports:extension.exports,require:n=>n==='vscode'?host:n.startsWith('./')?require('../'+n.slice(2)):require(n),Buffer,AbortController});
  const api=extension.exports.activate({subscriptions:[],extensionPath:root,extension:{packageJSON:{version:'0.3.0'}}});
  assert.equal(await api.chooseRoot(),undefined);
  assert.equal(await commands.get('edittrace.init')(),undefined);
  pick=1;assert.equal(await api.chooseRoot(),'/b');
});
test('invalid UTF-8 and oversized files are rejected before default regression running',async()=>workspace(async p=>{
  const saved=await project.save(p,fixture());
  await fs.writeFile(saved.file,Buffer.from([0x7b,0x22,0x78,0x22,0x3a,0x22,0xff,0x22,0x7d]));
  assert.equal((await project.discover(p))[0].status,'invalid');
  await assert.rejects(project.suite(p),/Invalid regression/);
  await fs.truncate(saved.file,8*1024*1024+1);
  assert.equal((await project.discover(p))[0].status,'invalid');
}));

/* Development-only capture: real Microsoft JSON language server and JSON-RPC tracer. */
'use strict';
const rpc = require('vscode-jsonrpc/node');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
async function main() {
  const [server, output] = process.argv.slice(2);
  if (!server || !output) throw new Error('Usage: node capture.cjs <installed jsonServerMain.js> <new-log.jsonl>');
  const child = spawn(process.execPath, [server, '--stdio'], {stdio: ['pipe', 'pipe', 'pipe'], windowsHide: true});
  const logs = [];
  let stderr = '';
  child.stderr.on('data', b => stderr += b);
  const connection = rpc.createMessageConnection(new rpc.StreamMessageReader(child.stdout), new rpc.StreamMessageWriter(child.stdin));
  connection.listen();
  connection.trace(rpc.Trace.Verbose, {log: record => {if (typeof record !== 'object') throw new Error('Expected JSON trace'); logs.push(record);}}, {traceFormat: rpc.TraceFormat.JSON, sendNotification: false});
  const timeout = setTimeout(() => {child.kill(); process.exitCode = 1;}, 20000);
  try {
    const initialized = await connection.sendRequest('initialize', {processId: process.pid, rootUri: null, capabilities: {general: {positionEncodings: ['utf-16']}, textDocument: {synchronization: {dynamicRegistration: false}}}});
    if (!initialized.capabilities) throw new Error('Invalid real server initialize response');
    await connection.sendNotification('initialized', {});
    const uri = 'file:///edittrace-capture-one.json';
    const second = 'file:///edittrace-capture-two.json';
    await connection.sendNotification('textDocument/didOpen', {textDocument: {uri, languageId: 'json', version: 1, text: '{"moon":"🌙"}'}});
    await connection.sendNotification('textDocument/didOpen', {textDocument: {uri: second, languageId: 'json', version: 1, text: '{}'}});
    await connection.sendNotification('textDocument/didChange', {textDocument: {uri, version: 2}, contentChanges: [{range: {start: {line: 0, character: 11}, end: {line: 0, character: 11}}, text: '!'}]});
    await connection.sendRequest('textDocument/formatting', {textDocument: {uri}, options: {tabSize: 2, insertSpaces: true}});
    await connection.sendNotification('textDocument/didClose', {textDocument: {uri: second}});
    await connection.sendNotification('textDocument/didOpen', {textDocument: {uri: second, languageId: 'json', version: 1, text: '{"reopened":true}'}});
    await connection.sendRequest('shutdown');
    await connection.sendNotification('exit');
    fs.writeFileSync(output, logs.map(j => JSON.stringify(j)).join('\n') + '\n', {flag: 'wx'});
    console.log(JSON.stringify({records: logs.length, tracer: 'vscode-jsonrpc@8.2.1', server, stderr}));
  } finally {clearTimeout(timeout); connection.dispose(); child.kill();}
}
main().catch(e => {console.error(e); process.exitCode = 1;});

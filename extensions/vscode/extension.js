'use strict';
const vscode = require('vscode');
const fs = require('node:fs/promises');
const path = require('node:path');
const {withInput} = require('./bridge');
const source = () => ({kind: 'editor_document_events', vscode: vscode.version, producer: 'edittrace-vscode/0.2.0'});
const plainRange = r => ({start: {line: r.start.line, character: r.start.character}, end: {line: r.end.line, character: r.end.character}});
const editJSON = e => ({range: plainRange(e.range), newText: e.newText});

class Recorder {
  constructor() {this.listeners = []; this.docs = new Map(); this.records = []; this.bytes = 0; this.error = null; this.active = false;}
  append(record) {
    if (this.records.length >= 100000 || this.bytes + Buffer.byteLength(JSON.stringify(record)) > 7 * 1024 * 1024) {
      this.error = 'recording resource limit'; this.dispose(); throw new Error(this.error);
    }
    if (record.kind !== 'meta') record.seq = this.records.length;
    this.bytes += Buffer.byteLength(JSON.stringify(record)); this.records.push(record);
  }
  message(method, params) {this.append({kind: 'message', direction: 'client_to_server', message: {jsonrpc: '2.0', method, params}});}
  open(doc) {
    if (!['file', 'untitled'].includes(doc.uri.scheme)) return;
    const uri = doc.uri.toString();
    if (this.docs.has(uri)) return;
    if (this.docs.size >= 64 || Buffer.byteLength(doc.getText()) > 4 * 1024 * 1024) throw new Error('document resource limit');
    this.docs.set(uri, {version: doc.version});
    this.message('textDocument/didOpen', {textDocument: {uri, languageId: doc.languageId, version: doc.version, text: doc.getText()}});
  }
  changed(event) {
    const doc = event.document, uri = doc.uri.toString(), previous = this.docs.get(uri);
    if (!previous) {if (!['file', 'untitled'].includes(doc.uri.scheme)) return; throw new Error('change without recorded baseline');}
    if (!event.contentChanges.length) return;
    if (doc.version !== previous.version + 1) throw new Error('document version gap; recording incomplete');
    // The host already supplies sequential application order, including ties.
    // Preserve it just as Microsoft's codeConverter does; sorting reverses ties.
    const changes = event.contentChanges;
    this.message('textDocument/didChange', {textDocument: {uri, version: doc.version}, contentChanges: changes.map(c => ({range: plainRange(c.range), text: c.text}))});
    this.append({kind: 'checkpoint', uri, version: doc.version, text: doc.getText(), source: 'vscode.TextDocument.getText.afterEvent'});
    previous.version = doc.version;
  }
  start() {
    if (this.active) throw new Error('Recording is already active');
    this.active = true;
    this.append({kind: 'meta', schema_version: 1, position_encoding: 'utf-16', capture_mode: 'fragment', provenance: 'captured', producer: 'edittrace-vscode/0.2.0', evidence_scope: 'editor_document_events', host_version: vscode.version});
    const guarded = fn => value => {try {fn(value);} catch(e) {this.error = e.message; this.dispose(); vscode.window.setStatusBarMessage('EditTrace stopped: recording incomplete. Use Stop Recording for details.', 10000);}};
    this.listeners.push(vscode.workspace.onDidOpenTextDocument(guarded(doc => this.open(doc))));
    this.listeners.push(vscode.workspace.onDidChangeTextDocument(guarded(e => this.changed(e))));
    this.listeners.push(vscode.workspace.onDidCloseTextDocument(guarded(doc => {const uri = doc.uri.toString(); if (this.docs.has(uri)) {this.message('textDocument/didClose', {textDocument: {uri}}); this.docs.delete(uri);}})));
    try {for (const doc of vscode.workspace.textDocuments) if (['file', 'untitled'].includes(doc.uri.scheme)) this.open(doc);}
    catch(e) {this.error = e.message; this.dispose(); throw e;}
  }
  stop() {this.dispose(); if (this.error) throw new Error(this.error); return this.records;}
  dispose() {this.active = false; for (const listener of this.listeners.splice(0)) listener.dispose();}
}

async function formattingPlan(doc) {
  const baseline = {uri: doc.uri.toString(), version: doc.version, text: doc.getText()};
  const edits = await vscode.commands.executeCommand('vscode.executeFormatDocumentProvider', doc.uri, {tabSize: 2, insertSpaces: true});
  if (!edits) throw new Error('No formatting edits returned: document may already be formatted or no provider is available');
  if (doc.version !== baseline.version) throw new Error('Document changed while computing formatting');
  return {schema_version: 1, kind: 'edit_plan', position_encoding: 'utf-16', source: {...source(), kind: 'format_provider'}, documents: [baseline], workspace_edit: {documentChanges: [{textDocument: {uri: baseline.uri, version: baseline.version}, edits: edits.map(editJSON)}]}};
}
async function renamePlan(doc, position, name) {
  const before = new Map(vscode.workspace.textDocuments.map(d => [d.uri.toString(), d.version]));
  const changes = await vscode.commands.executeCommand('vscode.executeDocumentRenameProvider', doc.uri, position, name);
  if (!changes) throw new Error('No rename provider returned edits');
  const documents = [], documentChanges = [];
  for (const [uri, edits] of changes.entries()) {
    if (uri.scheme !== 'file') throw new Error('Only local text documents are supported');
    const d = await vscode.workspace.openTextDocument(uri);
    if (before.has(uri.toString()) && before.get(uri.toString()) !== d.version) throw new Error('Document changed while computing rename');
    documents.push({uri: uri.toString(), version: d.version, text: d.getText()});
    documentChanges.push({textDocument: {uri: uri.toString(), version: null}, edits: edits.map(editJSON)});
  }
  if (!documents.length) throw new Error('Rename returned no text edits');
  // Stable API exposes text entries, not all resource operations. Scope is explicit.
  return {schema_version: 1, kind: 'edit_plan', position_encoding: 'utf-16', source: {...source(), kind: 'rename_provider_text_projection', limitation: 'Only text entries are verified; resource operations and provider base versions are not verified.'}, documents, workspace_edit: {documentChanges}};
}

function makeCaseDraft(last) {
  if (!last || last.report.analysis_complete !== true) throw new Error('Complete an analysis before saving a regression case');
  const input = last.kind === 'trace' ? {kind: 'trace', records: last.records} : {kind: 'edit_plan', plan: last.plan};
  const texts = last.kind === 'edit_plan' ? last.report.documents.map(d => ({uri: d.uri, text: d.text})) : last.records.filter(r => r.kind === 'checkpoint').map(r => ({uri: r.uri, text: r.text, at_seq: r.seq}));
  return {schema_version: 1, kind: 'case', name: 'editor-capture', source: source(), input, expect: {analysis_complete: true, exit_code: last.report.exit_code, texts, findings: last.report.findings.map(f => ({rule_id: f.rule_id, uri: f.uri}))}};
}

function activate(context) {
  let recorder, last;
  const executable = () => vscode.workspace.getConfiguration('edittrace').get('executablePath', '') || path.join(context.extensionPath, 'bin', process.platform === 'win32' ? 'edittrace.exe' : 'edittrace');
  async function show(report) {const d = await vscode.workspace.openTextDocument({content: JSON.stringify(report, null, 2), language: 'json'}); await vscode.window.showTextDocument(d);}
  function register(name, fn) {context.subscriptions.push(vscode.commands.registerCommand(name, async () => {try {return await fn();} catch(e) {void vscode.window.showErrorMessage(`EditTrace: ${e.message}`); throw e;}}));}
  async function analyze(command, input) {
    return vscode.window.withProgress({location: vscode.ProgressLocation.Notification, title: 'EditTrace: analyzing', cancellable: true}, async (_, token) => {
      const controller = new AbortController(), listener = token.onCancellationRequested(() => controller.abort());
      try {return await withInput(executable(), command, input, {signal: controller.signal});} finally {listener.dispose();}
    });
  }
  register('edittrace.start', () => {if (recorder?.active) throw new Error('Recording is already active'); recorder = new Recorder(); recorder.start(); vscode.window.setStatusBarMessage('EditTrace recording open documents; use Stop Recording to finish.');});
  register('edittrace.stop', async () => {
    if (!recorder) throw new Error('No recording');
    const records = recorder.stop();
    const {report} = await analyze('audit', records);
    last = {kind: 'trace', records, report}; await show(report);
    vscode.window.setStatusBarMessage('EditTrace recording stopped.', 3000);
  });
  async function preview(plan) {if (recorder?.active) throw new Error('Stop recording before previewing edits'); const {report} = await analyze('check-edits', plan); last = {kind: 'edit_plan', plan, report}; await show(report);}
  register('edittrace.format', async () => {const e = vscode.window.activeTextEditor; if (!e) throw new Error('Open a document first'); await preview(await formattingPlan(e.document));});
  register('edittrace.rename', async () => {const e = vscode.window.activeTextEditor; if (!e) throw new Error('Open a document first'); const name = await vscode.window.showInputBox({prompt: 'New symbol name (text edits only; file operations are not verified)'}); if (name) await preview(await renamePlan(e.document, e.selection.active, name));});
  register('edittrace.saveCase', async () => {
    if (!last) throw new Error('Analyze a recording or edit plan first');
    if (last.report.analysis_complete !== true) throw new Error('Incomplete analysis cannot become a passing regression case');
    const target = await vscode.window.showSaveDialog({filters: {'EditTrace case': ['json']}, saveLabel: 'Save explicit expectations'});
    if (!target) return;
    const draft = makeCaseDraft(last);
    // Show draft before saving; recorded/predicted outputs are not independent golden truth.
    const choice = await vscode.window.showWarningMessage('Review these recorded expectations before treating them as a correctness oracle.', {modal: true}, 'Save draft for review');
    if (!choice) return;
    await fs.writeFile(target.fsPath, JSON.stringify(draft, null, 2) + '\n', {flag: 'wx'});
    await vscode.window.showTextDocument(await vscode.workspace.openTextDocument(target));
  });
  register('edittrace.diff', async () => {
    if (last?.kind !== 'edit_plan' || !last.report.documents.length) throw new Error('Preview text edits first');
    const d = last.report.documents[0], baseline = last.plan.documents.find(b => b.uri === d.uri);
    const before = await vscode.workspace.openTextDocument({content: baseline.text});
    const after = await vscode.workspace.openTextDocument({content: d.text});
    await vscode.commands.executeCommand('vscode.diff', before.uri, after.uri, 'EditTrace: baseline ↔ predicted text');
  });
  context.subscriptions.push({dispose() {recorder?.dispose();}});
  return {Recorder, formattingPlan, renamePlan, withInput, makeCaseDraft};
}
module.exports = {activate, Recorder, formattingPlan, renamePlan, makeCaseDraft};

'use strict';
const vscode = require('vscode');
const fs = require('node:fs/promises');
const path = require('node:path');
const {Recorder} = require('./extension');
const {withInput} = require('./bridge');
const {providerCall, ProviderTimeout} = require('./diagnostics');

const fields = range => ({
  start: {line: range.start.line, character: range.start.character},
  end: {line: range.end.line, character: range.end.character},
});

async function observe(scenario, root) {
  const documents = new Map();
  for (const file of scenario.files) {
    const doc = await vscode.workspace.openTextDocument(vscode.Uri.joinPath(root, file.path));
    if (doc.getText() !== file.before) throw new Error('Host baseline differs: ' + file.path);
    documents.set(doc.uri.toString(), {doc, file, version: doc.version});
  }
  const uri = vscode.Uri.joinPath(root, scenario.operation.path);
  const {doc} = documents.get(uri.toString());
  if (doc.languageId !== scenario.language) throw new Error('Unexpected document language');
  const baseline = [...documents.values()].map(({doc: d, version, file}) => ({
    uri: d.uri.toString(), version, text: file.before,
  }));
  const op = scenario.operation;
  let verification;
  if (op.kind === 'sync') {
    const recorder = new Recorder();
    recorder.start();
    try {
      // The candidate-owned command must resolve after completing its editor actions.
      await vscode.window.showTextDocument(doc);
      await providerCall(() => vscode.commands.executeCommand(op.command));
    } finally {
      recorder.stop();
    }
    for (const {doc: d} of documents.values()) {
      recorder.append({
        kind: 'checkpoint', uri: d.uri.toString(), version: d.version,
        text: d.getText(), source: 'vscode.TextDocument.getText.afterCommand',
      });
    }
    verification = {kind: 'trace', records: recorder.records};
  } else {
    if (op.kind === 'rename') {
      const position = new vscode.Position(op.line, op.character);
      if (!doc.validatePosition(position).isEqual(position)) throw new Error('Rename position is outside the fixture');
    }
    const entries = op.kind === 'format'
      ? [[uri, await providerCall(() => vscode.commands.executeCommand(
        'vscode.executeFormatDocumentProvider', uri, {tabSize: 2, insertSpaces: true}))]]
      : (await providerCall(() => vscode.commands.executeCommand(
        'vscode.executeDocumentRenameProvider', uri,
        new vscode.Position(op.line, op.character), op.new_name)))?.entries();
    if (!entries || entries.some(([, edits]) => !Array.isArray(edits))) {
      throw new ProviderResponseUnavailable();
    }
    if ([...documents.values()].some(d => d.doc.version !== d.version)) {
      throw new Error('Document changed while provider was computing edits');
    }
    const edit = new vscode.WorkspaceEdit();
    const operations = [];
    for (const [target, edits] of entries) {
      if (!edits.length) continue;
      if (!documents.has(target.toString())) {
        return {unexpected: true, failures: [{reason: 'provider edit outside declared files'}]};
      }
      // Stable VS Code APIs expose the text projection. Apply only those entries.
      edit.set(target, edits);
      operations.push({
        textDocument: {uri: target.toString(), version: documents.get(target.toString()).version},
        edits: edits.map(e => ({range: fields(e.range), newText: e.newText})),
      });
    }
    if (!operations.length) throw new ProviderResponseUnavailable();
    if (operations.length && !await vscode.workspace.applyEdit(edit)) throw new Error('Host refused candidate edits');
    verification = {kind: 'edit_plan', plan: {
      schema_version: 1, kind: 'edit_plan', position_encoding: 'utf-16',
      source: {kind: 'fresh_vscode_provider_text_projection'},
      documents: baseline,
      workspace_edit: {documentChanges: operations},
      actual: operations.map(({textDocument}) => ({
        uri: textDocument.uri, text: documents.get(textDocument.uri).doc.getText(),
      })),
    }};
  }
  const observed = [...documents.values()].map(({file, doc: d}) => ({
    path: file.path, uri: d.uri.toString(), text: d.getText(),
  }));
  // Check the isolated workspace for direct writes and undeclared file changes.
  const remaining = new Map(scenario.files.map(f => [f.path, f.before]));
  async function scan(dir, prefix = '') {
    for (const entry of await fs.readdir(dir, {withFileTypes: true})) {
      const name = prefix + entry.name;
      const item = path.join(dir, entry.name);
      if (entry.isDirectory() && [...remaining.keys()].some(p => p.startsWith(name + '/'))) {
        if (!await scan(item, name + '/')) return false;
      } else if (!entry.isFile() || !remaining.has(name) ||
        (await fs.stat(item)).size > 256 * 1024 ||
        !(await fs.readFile(item)).equals(Buffer.from(remaining.get(name)))) {
        return false;
      } else {
        remaining.delete(name);
      }
    }
    return true;
  }
  if (!await scan(root.fsPath) || remaining.size) {
    return {unexpected: true, failures: [{reason: 'provider changed files on disk'}]};
  }
  return {
    schema_version: 2, kind: 'provider_observation', name: scenario.name,
    expected: scenario.files.map(f => ({path: f.path, text: f.after})), observed, verification,
  };
}

class ProviderResponseUnavailable extends Error {}

async function run() {
  const request = JSON.parse(await fs.readFile(process.env.EDITTRACE_PROVIDER_REQUEST, 'utf8'));
  const {scenario, candidate} = request;
  let report;
  let stage = 'host_version';
  try {
    if (request.report_protocol !== 2) throw new Error('Unsupported report protocol');
    if (vscode.version !== request.host) throw new Error('Unexpected VS Code host version');
    stage = 'candidate_activation';
    const extension = vscode.extensions.getExtension(candidate.id);
    if (!extension || extension.packageJSON.version !== candidate.version ||
        path.resolve(extension.extensionPath) !== path.resolve(request.installed)) {
      throw new Error('Active candidate installation does not match requested artifact');
    }
    await providerCall(() => extension.activate());
    stage = 'provider_request';
    const root = vscode.workspace.workspaceFolders[0].uri;
    const observation = await observe(scenario, root);
    stage = 'core_verification';
    report = observation.unexpected
      ? {exit_code: 1, analysis_complete: true, failures: observation.failures}
      : (await withInput(request.core, 'check-provider', observation)).report;
    stage = report.exit_code === 2 ? 'core_verification' : 'complete';
  } catch (error) {
    // Provider exceptions can contain source or paths. Keep diagnostics local.
    await fs.writeFile(request.log, Buffer.from(String(error.stack || error)).subarray(0, 256 * 1024), {flag: 'wx'});
    const reason = error instanceof ProviderResponseUnavailable ? 'provider response unavailable'
      : error instanceof ProviderTimeout ? 'provider request timed out' : 'host or provider execution incomplete';
    report = {exit_code: 2, analysis_complete: false, failures: [{reason}]};
  }
  const result = {
    report_protocol: 2, request_id: request.request_id, candidate,
    name: scenario.name, host: vscode.version, stage,
    exit_code: report.exit_code, analysis_complete: report.analysis_complete,
    failures: report.failures, rules: report.rules ?? [],
  };
  await fs.writeFile(request.result, JSON.stringify(result), {flag: 'wx'});
}

module.exports = {run};

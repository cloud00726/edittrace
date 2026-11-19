'use strict';
const vscode = require('vscode');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');

function activate(context) {
  const pin = context.extension.packageJSON.edittraceTypeScript;
  const runtime = process.env.EDITTRACE_TYPESCRIPT_JS;
  if (!runtime || !path.isAbsolute(runtime) ||
      createHash('sha256').update(fs.readFileSync(runtime)).digest('hex') !== pin.sha256) {
    throw new Error('TypeScript runtime does not match the verified candidate');
  }
  const ts = require(runtime);
  if (ts.version !== pin.version) throw new Error('Unexpected TypeScript runtime version');

  async function rename(document, position, newName) {
    const root = vscode.workspace.getWorkspaceFolder(document.uri).uri;
    const key = uri => uri.fsPath.split(path.sep).join('/');
    const files = new Map();
    for (const uri of await vscode.workspace.findFiles(new vscode.RelativePattern(root, '**/*.ts'))) {
      files.set(key(uri), await vscode.workspace.openTextDocument(uri));
    }
    const names = [...files.keys()].sort();
    const directoryExists = name => names.some(file => file.startsWith(name.replace(/\/$/, '') + '/'));
    const host = {
      getCompilationSettings: () => ({noLib: true, moduleResolution: ts.ModuleResolutionKind.Node10}),
      getScriptFileNames: () => names,
      getScriptVersion: name => String(files.get(name)?.version ?? 0),
      getScriptSnapshot: name => files.has(name) ? ts.ScriptSnapshot.fromString(files.get(name).getText()) : undefined,
      getCurrentDirectory: () => key(root),
      getDefaultLibFileName: opts => ts.getDefaultLibFilePath(opts),
      fileExists: name => files.has(name),
      readFile: name => files.get(name)?.getText(),
      directoryExists,
      useCaseSensitiveFileNames: () => true,
    };
    const service = ts.createLanguageService(host);
    const source = key(document.uri);
    const offset = document.offsetAt(position);
    try {
      if (!service.getRenameInfo(source, offset).canRename) return undefined;
      const locations = service.findRenameLocations(source, offset, false, false, true);
      if (!locations?.length) return undefined;
      const changed = new vscode.WorkspaceEdit();
      for (const {fileName, textSpan, prefixText, suffixText} of locations) {
        if (pin.synthetic_omit_reference && fileName !== source) continue;
        const target = files.get(fileName);
        if (!target || textSpan.start < 0 || textSpan.start + textSpan.length > target.getText().length) {
          throw new Error('TypeScript location falls outside the available source files');
        }
        changed.replace(target.uri, new vscode.Range(target.positionAt(textSpan.start),
          target.positionAt(textSpan.start + textSpan.length)), (prefixText ?? '') + newName + (suffixText ?? ''));
      }
      return changed;
    } finally {
      service.dispose();
    }
  }

  return {edittraceProviderV1: {rename}};
}

module.exports = {activate};

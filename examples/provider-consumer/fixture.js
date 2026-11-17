'use strict';
const vscode = require('vscode');

function activate(context) {
  const version = context.extension.packageJSON.version;
  const fault = version === '1.1.0';
  const selector = {language: 'edittrace-fixture', scheme: 'file'};
  const format = () => {
    if (version === '1.3.0') return new Promise(() => {});
    return [vscode.TextEdit.replace(new vscode.Range(0, 3, 0, 5), fault ? '' : ' ')];
  };
  context.subscriptions.push(
    vscode.languages.registerRenameProvider(selector, {
      provideRenameEdits(doc, position, newName) {
        const edits = new vscode.WorkspaceEdit();
        const range = new vscode.Range(position.line, position.character, position.line, position.character + 3);
        edits.replace(doc.uri, range, newName);
        if (!fault) {
          const root = vscode.workspace.getWorkspaceFolder(doc.uri).uri;
          edits.replace(vscode.Uri.joinPath(root, 'reference.etrf'), range, newName);
        }
        return edits;
      },
    }),
    vscode.commands.registerCommand('edittrace-fixture.sync', async () => {
      const editor = vscode.window.activeTextEditor;
      if (!await editor.edit(edit => edit.replace(new vscode.Range(0, 0, 0, 1), 'A'))) {
        throw new Error('Initial sync action failed');
      }
      if (!fault && !await editor.edit(edit => edit.insert(new vscode.Position(0, 3), '!'))) {
        throw new Error('Second sync action failed');
      }
    }),
  );
  if (version !== '1.2.0') {
    context.subscriptions.push(vscode.languages.registerDocumentFormattingEditProvider(selector, {
      provideDocumentFormattingEdits: format,
    }));
  }
  // 1.4.0 still responds to the global VS Code formatter command. A suite
  // requesting the candidate API must nevertheless reject it.
  if (version !== '1.2.0' && version !== '1.4.0') return {edittraceProviderV1: {format}};
}

module.exports = {activate};

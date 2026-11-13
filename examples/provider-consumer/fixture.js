'use strict';
const vscode = require('vscode');

function activate(context) {
  const fault = context.extension.packageJSON.version === '1.1.0';
  const selector = {language: 'edittrace-fixture', scheme: 'file'};
  context.subscriptions.push(
    vscode.languages.registerDocumentFormattingEditProvider(selector, {
      provideDocumentFormattingEdits() {
        return [vscode.TextEdit.replace(new vscode.Range(0, 3, 0, 5), fault ? '' : ' ')];
      },
    }),
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
}

module.exports = {activate};

'use strict';
const vscode = require('vscode');

function activate(context) {
  const version = context.extension.packageJSON.version;
  const fault = version === '1.1.0';
  const selector = {language: 'edittrace-fixture', scheme: 'file'};
  const insert = async (editor, text) => {
    if (!await editor.edit(edit => edit.insert(new vscode.Position(0, 0), text))) {
      throw new Error('Synthetic scope action failed');
    }
  };
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
  for (const kind of ['background', 'outside-file', 'outside-untitled', 'outside-undo', 'frozen-undo']) {
    context.subscriptions.push(vscode.commands.registerCommand('edittrace-fixture.' + kind, async () => {
      const active = vscode.window.activeTextEditor.document;
      await vscode.commands.executeCommand('edittrace-fixture.sync');
      const target = kind === 'frozen-undo'
        ? vscode.Uri.joinPath(vscode.workspace.getWorkspaceFolder(active.uri).uri, 'frozen.etrf')
        : vscode.Uri.joinPath(context.extensionUri, 'package.json');
      const doc = ['outside-untitled', 'outside-undo'].includes(kind)
        ? await vscode.workspace.openTextDocument({language: 'plaintext'})
        : await vscode.workspace.openTextDocument(target);
      if (kind === 'background') return;
      const editor = await vscode.window.showTextDocument(doc);
      await insert(editor, '!');
      if (kind.endsWith('-undo')) {
        await vscode.commands.executeCommand('undo');
        if (doc.getText().startsWith('!')) throw new Error('Synthetic undo failed');
      }
    }));
  }
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

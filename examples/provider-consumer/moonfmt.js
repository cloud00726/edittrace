'use strict';
const vscode = require('vscode');
const fs = require('node:fs');
const path = require('node:path');
const {createHash} = require('node:crypto');
const {spawnSync} = require('node:child_process');

function activate(context) {
  return {edittraceProviderV1: {
    format(document) {
      const executable = process.env.EDITTRACE_MOONFMT_EXE;
      if (!executable || !path.isAbsolute(executable)) throw new Error('Set EDITTRACE_MOONFMT_EXE to the pinned formatter');
      const configuredHash = context.extension.packageJSON.edittraceMoonfmtSha256;
      const digest = createHash('sha256').update(fs.readFileSync(executable)).digest('hex');
      if (digest !== configuredHash) throw new Error('Moonfmt executable does not match the adapter');
      const result = spawnSync(executable, ['-'], {
        input: document.getText(), encoding: 'utf8', timeout: 10000,
        maxBuffer: 256 * 1024, windowsHide: true,
      });
      if (result.error || result.status !== 0) throw new Error('Moonfmt execution failed');
      const eol = document.eol === vscode.EndOfLine.CRLF ? '\r\n' : '\n';
      const text = result.stdout.replace(/\r?\n/g, eol);
      return [vscode.TextEdit.replace(new vscode.Range(
        document.positionAt(0), document.positionAt(document.getText().length)), text)];
    },
  }};
}

module.exports = {activate};

'use strict';
const {spawn} = require('node:child_process');
const fs = require('node:fs/promises');
const path = require('node:path');
const os = require('node:os');

// Transport only: all validation and result computation stays in MoonBit.
async function invoke(executable, args, {signal, timeout = 30000} = {}) {
  if (!path.isAbsolute(executable)) throw new Error('Configure an absolute edittrace.executablePath.');
  if (signal?.aborted) throw new Error('EditTrace canceled');
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, {shell: false, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
    const output = [], errors = [];
    let total = 0, terminalError;
    const cancel = () => { terminalError = new Error('EditTrace canceled'); child.kill(); };
    signal?.addEventListener('abort', cancel, {once: true});
    const timer = setTimeout(() => { terminalError = new Error('EditTrace timed out'); child.kill(); }, timeout);
    function collect(target, chunk) {
      total += chunk.length;
      if (total > 32 * 1024 * 1024) { terminalError = new Error('EditTrace output limit'); child.kill(); }
      else target.push(chunk);
    }
    child.stdout.on('data', b => collect(output, b));
    child.stderr.on('data', b => collect(errors, b));
    const cleanup = () => {clearTimeout(timer); signal?.removeEventListener('abort', cancel);};
    child.on('error', e => {cleanup(); reject(e);});
    child.on('close', code => {
      cleanup();
      if (terminalError) return reject(terminalError);
      const stdout = Buffer.concat(output).toString('utf8'), stderr = Buffer.concat(errors).toString('utf8');
      if (code !== 0 && code !== 1) return reject(new Error(stderr || `EditTrace failed with exit ${code}`));
      try {
        const report = JSON.parse(stdout);
        if (!report || report.exit_code !== code) return reject(new Error('EditTrace report and process status disagree'));
        resolve({code, report});
      }
      catch { reject(new Error('EditTrace returned invalid JSON')); }
    });
  });
}
async function withInput(executable, command, value, options) {
  const directory = await fs.mkdtemp(path.join(os.tmpdir(), 'edittrace-'));
  try {
    const file = path.join(directory, 'input.json');
    const raw = command === 'audit' ? value.map(x => JSON.stringify(x)).join('\n') + '\n' : JSON.stringify(value);
    if (Buffer.byteLength(raw) > 8 * 1024 * 1024) throw new Error('EditTrace input exceeds 8 MiB');
    await fs.writeFile(file, raw, {flag: 'wx'});
    return await invoke(executable, [...(Array.isArray(command) ? command : [command]), file, '--format', 'json'], options);
  } finally { await fs.rm(directory, {recursive: true, force: true}); }
}
module.exports = {invoke, withInput};

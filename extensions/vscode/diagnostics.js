'use strict';
const {invoke} = require('./bridge');

async function diagnose(executable, host, options) {
  let report;
  try { ({report} = await invoke(executable, ['doctor', '--format', 'json'], options)); }
  catch (e) {
    if (e.code === 'ENOENT') throw new Error('Core executable not found. Install the matching platform VSIX or configure an absolute edittrace.executablePath.');
    throw new Error(`Core diagnosis failed: ${e.message}. Use a core supporting doctor and bridge protocol 1.`);
  }
  checkCapabilities(report);
  return {...report, executable, ...host, compatible: true};
}
function checkCapabilities(report) {
  if (report.kind !== 'doctor_report' || report.bridge_protocol !== 1 || report.case_schema !== 1 || report.position_encoding !== 'utf-16') {
    throw new Error('Incompatible core capabilities. This extension requires bridge protocol 1, UTF-16 and case schema 1.');
  }
}

async function providerCall(run, timeout = 15000) {
  let timer;
  try {
    return await Promise.race([
      Promise.resolve().then(run).catch(e => { throw new Error(`Provider failed: ${e.message}`); }),
      new Promise((_, reject) => { timer = setTimeout(() => reject(new Error('Provider timed out. Retry after the language service is ready; no edits were applied.')), timeout); })
    ]);
  } finally { clearTimeout(timer); }
}
module.exports = {diagnose, providerCall,checkCapabilities};

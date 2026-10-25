'use strict';
// Presentation checks only. Text calculations and result summaries come from MoonBit.
function reportText(report) {
  if (!report || typeof report !== 'object' || ![0,1,2].includes(report.exit_code) || typeof report.analysis_complete !== 'boolean') throw new Error('Malformed core report status');
  if (typeof report.display_summary !== 'string') throw new Error('Core report lacks the summary capability; use the matching release core.');
  // JSON escaping prevents control sequences and bidi controls in untrusted labels.
  const safe = report.display_summary.replace(/[\x00-\x08\x0b-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]/g,c=>'\\u'+c.charCodeAt(0).toString(16).padStart(4,'0'));
  return 'EditTrace result\n' + safe + '\nUse EditTrace: Show Raw JSON Report for full local evidence.\n';
}
function diffChoices(last) {
  if (last?.kind !== 'edit_plan' || !Array.isArray(last.report.documents)) throw new Error('Preview text edits first');
  return last.report.documents.map((d, index) => {
    const b = last.plan.documents.find(x => x.uri === d.uri);
    if (!b || typeof b.text !== 'string' || typeof d.text !== 'string') throw new Error('Malformed document/baseline in core report');
    if (d.actual_compared && typeof d.actual_text !== 'string') throw new Error('Malformed independent actual text');
    return {label: JSON.stringify(d.uri), description: d.actual_compared ? 'Independent actual available' : 'Prediction only; actual unavailable', index, document:d, baseline:b};
  });
}
module.exports = {reportText, diffChoices};

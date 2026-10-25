'use strict';
const fs = require('node:fs/promises');
const path = require('node:path');
const crypto = require('node:crypto');
const {TextDecoder} = require('node:util');
const MAX = 8 * 1024 * 1024;
const digest = b => crypto.createHash('sha256').update(b).digest('hex');
const parse = bytes => JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
const names = n => typeof n === 'string' && /^case-[a-zA-Z0-9-]+\.json$/.test(n);

async function directory(root, create = false) {
  const base = await fs.realpath(root), dir = path.join(base, '.edittrace');
  if (create) await fs.mkdir(dir).catch(e => {if (e.code !== 'EEXIST') throw e;});
  const stat = await fs.lstat(dir);
  if (!stat.isDirectory() || stat.isSymbolicLink() || await fs.realpath(dir) !== dir) throw new Error('Regression directory must be a real local .edittrace directory, not a link');
  return dir;
}
async function read(dir, name) {
  if (path.basename(name) !== name) throw new Error('Regression path escape rejected');
  const file = path.join(dir, name), stat = await fs.lstat(file);
  if (!stat.isFile() || stat.isSymbolicLink() || stat.size > MAX) throw new Error('Regression file must be a bounded regular file');
  const h = await fs.open(file, 'r');
  try {
    const opened = await h.stat();
    if (!opened.isFile() || opened.ino !== stat.ino || opened.dev !== stat.dev || opened.size > MAX) throw new Error('Regression file changed while opening');
    // A bounded read protects against files growing after stat.
    const bytes = Buffer.alloc(MAX + 1); let length = 0;
    while (length < bytes.length) {const r = await h.read(bytes, length, bytes.length - length, null); if (!r.bytesRead) break; length += r.bytesRead;}
    if (length > MAX) throw new Error('Regression file exceeds 8 MiB');
    return bytes.subarray(0, length);
  } finally {await h.close();}
}
async function init(root) {
  const dir = await directory(root, true);
  await fs.writeFile(path.join(dir,'project.json'),JSON.stringify({schema_version:1,kind:'regression_project',case_pattern:'case-*.json',run_policy:'unchanged_confirmed_only'},null,2)+'\n',{flag:'wx'}).catch(e=>{if(e.code!=='EEXIST')throw e;});
  await fs.writeFile(path.join(dir,'README.md'), '# EditTrace regressions\n\nSave drafts, review the complete input and expectations, then explicitly confirm. Only unchanged confirmed cases enter the default suite. CLI v1 cases remain directly runnable. Files may contain source text.\n', {flag:'wx'}).catch(e=>{if(e.code!=='EEXIST')throw e;});
  return dir;
}
async function save(root, draft) {
  const dir = await init(root), name = 'case-' + crypto.randomUUID() + '.json';
  const bytes = Buffer.from(JSON.stringify(draft,null,2)+'\n');
  if (bytes.length > MAX) throw new Error('Regression case exceeds 8 MiB');
  await fs.writeFile(path.join(dir,name), bytes, {flag:'wx'});
  await fs.writeFile(path.join(dir,name+'.review.json'), JSON.stringify({schema_version:1,status:'draft',sha256:digest(bytes),source:draft.source},null,2)+'\n', {flag:'wx'});
  return {name, file:path.join(dir,name)};
}
async function discover(root) {
  const dir = await directory(root);
  const config=parse(await read(dir,'project.json'));
  if(config.schema_version!==1 || config.kind!=='regression_project' || config.case_pattern!=='case-*.json' || config.run_policy!=='unchanged_confirmed_only')throw new Error('Unsupported regression project configuration');
  const files = [];
  for await (const entry of await fs.opendir(dir)) {
    if(files.length>=1024)throw new Error('Regression directory entry limit (1024)');
    files.push(entry.name);
  }
  const cases = files.filter(names).sort();
  if (cases.length > 256) throw new Error('Regression case limit (256)');
  const result = [];
  let total = 0;
  for (const name of cases) {
    try {
      const raw = await read(dir,name);
      total += raw.length;
      if(total > 64*1024*1024)throw new Error('Regression discovery exceeds 64 MiB');
      const value = parse(raw);
      const meta = parse(await read(dir,name+'.review.json'));
      if (meta.schema_version !== 1 || !['draft','confirmed'].includes(meta.status) || typeof meta.sha256 !== 'string') throw new Error('Malformed review metadata');
      result.push({name,file:path.join(dir,name),value,sha256:digest(raw),previousExpect:meta.reviewed_expect,status:meta.sha256 === digest(raw) ? meta.status : 'changed'});
    } catch(e) { result.push({name,file:path.join(dir,name),status:'invalid',error:e.message}); }
    if(total > 64*1024*1024)throw new Error('Regression discovery exceeds 64 MiB');
  }
  return result;
}
async function confirm(root, name, reviewedHash) {
  if (!names(name)) throw new Error('Invalid regression case name');
  const dir = await directory(root), raw = await read(dir,name);
  if (digest(raw) !== reviewedHash) throw new Error('Case changed during review; reopen and review again');
  const meta = parse(await read(dir,name+'.review.json'));
  if (meta.schema_version !== 1 || !['draft','confirmed'].includes(meta.status) || typeof meta.sha256 !== 'string') throw new Error('Malformed review metadata');
  const confirmation = {schema_version:1,status:'confirmed',sha256:reviewedHash,source:meta.source,reviewed_expect:parse(raw).expect};
  const temp = path.join(dir,'.review-'+crypto.randomUUID());
  try { await fs.writeFile(temp, JSON.stringify(confirmation,null,2)+'\n',{flag:'wx'}); await fs.rename(temp,path.join(dir,name+'.review.json')); }
  finally {await fs.unlink(temp).catch(e=>{if(e.code!=='ENOENT')throw e;});}
}
async function suite(root) {
  const entries = await discover(root);
  const invalid = entries.filter(e=>e.status === 'invalid');
  if (invalid.length) throw new Error('Invalid regression metadata/input: '+invalid.map(e=>e.name).join(', '));
  const confirmed = entries.filter(e=>e.status==='confirmed');
  if (!confirmed.length) throw new Error('No unchanged confirmed cases. Review drafts or changed cases explicitly first.');
  const value = {schema_version:1,kind:'suite',cases:confirmed.map(e=>e.value)};
  if (Buffer.byteLength(JSON.stringify(value)) > MAX) throw new Error('Combined suite exceeds 8 MiB; run cases individually');
  return {value, entries:confirmed, excluded:entries.filter(e=>e.status!=='confirmed').map(e=>({name:e.name,status:e.status}))};
}
module.exports = {init,save,discover,confirm,suite,directory};

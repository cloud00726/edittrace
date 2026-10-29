"""Stage an explicit source-package allowlist, then run the pinned moon package locally."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
    destination=Path(a.out).resolve();destination.mkdir(parents=True,exist_ok=False)
    # A stage under ignored output/ inherits the repository ignore and moon can
    # silently produce an empty archive. Use a fresh directory outside its ancestry.
    stage=Path(tempfile.mkdtemp(prefix='edittrace-source-stage-'))
    (stage/'.gitignore').write_text('.mooncakes/\n_build/\n',encoding='utf-8')
    for name in ['core','adapters','io','cmd','tests']:
        shutil.copytree(ROOT/name,stage/name,ignore=shutil.ignore_patterns('_build','__pycache__'))
    for name in ['moon.mod','LICENSE','THIRD_PARTY_NOTICES.md']:
        shutil.copy2(ROOT/name,stage/name)
    (stage/'docs').mkdir()
    for name in ['API.md','CLI.md','PROTOCOL_NOTES.md','TRACE_FORMAT.md','LIMITATIONS.md','STAGE2_SPEC.md']:
        shutil.copy2(ROOT/'docs'/name,stage/'docs'/name)
    shutil.copy2(ROOT/'docs/MOONCAKES_README.md',stage/'README.md')
    home=Path(os.environ.get('MOON_HOME',ROOT/'.tooling/moon')).resolve()
    moon=home/'bin'/('moon.exe' if os.name=='nt' else 'moon')
    env=os.environ.copy();env['MOON_HOME']=str(home)
    # Use the already pinned runtime cache; it is excluded from moon's package file list.
    shutil.copytree(ROOT/'.mooncakes',stage/'.mooncakes')
    p=subprocess.run([str(moon),'package','--frozen'],cwd=stage,env=env,capture_output=True,timeout=180)
    (destination/'package.log').write_bytes(p.stdout+p.stderr)
    if p.returncode:raise SystemExit('Source candidate failed: inspect package.log')
    archives=list((stage/'_build/publish').glob('*.zip'))
    if len(archives)!=1:raise RuntimeError('Ambiguous source archive')
    archive=destination/archives[0].name;shutil.copy2(archives[0],archive)
    with zipfile.ZipFile(archive) as z:
        files=[n.replace('\\','/') for n in z.namelist()]
        if not files:raise RuntimeError('Empty source candidate; check inherited ignore rules')
        if z.testzip() is not None:raise RuntimeError('Source ZIP CRC failed')
        forbidden=['.git/','.tooling/','.mooncakes/','artifacts/','output/','credentials','host-validation.json']
        if any(any(x in n.replace('\\','/').lower() for x in forbidden) for n in files):raise RuntimeError('Unexpected local data in source candidate')
        if not any(n.endswith('/LICENSE') or n=='LICENSE' for n in files):raise RuntimeError('Missing source license')
    evidence={'archive':archive.name,'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'files':files,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'namespace':'local/edittrace; replace only after verified account ownership','published':False,'generated_by':'pinned moon package --frozen from explicit allowlist outside repository ignore ancestry'}
    (destination/'source-manifest.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'archive':str(archive),'files':len(files),'published':False}))


if __name__=='__main__':main()

"""Explicit registry-only smoke test. Never publishes or substitutes a local workspace."""
import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--module', required=True, help='Actual published owner/module, not local/edittrace')
    ap.add_argument('--version', required=True)
    args = ap.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+/[A-Za-z0-9_-]+',args.module) or args.module.startswith('local/'):
        ap.error('Use the verified published namespace/module')
    if not re.fullmatch(r'\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',args.version):
        ap.error('Use an explicit published semantic version')
    home=Path(os.environ.get('MOON_HOME',ROOT/'.tooling/moon')).resolve()
    moon=home/'bin'/('moon.exe' if os.name=='nt' else 'moon')
    # System temp lies outside repository ancestors, so moon.work cannot replace registry input.
    directory=Path(tempfile.mkdtemp(prefix='edittrace-registry-consumer-'))
    (directory/'moon.mod').write_text('name = "consumer/registry_smoke"\nimport { "'+args.module+'@'+args.version+'", }\n',encoding='utf-8')
    (directory/'moon.pkg').write_text('import { "'+args.module+'/core/edit_plan", }\npkgtype(kind: "executable")\n',encoding='utf-8')
    (directory/'main.mbt').write_text('fn main { match @edit_plan.evaluate("unchanged", []) { Applied(s) => println(s); Rejected(_) => panic() } }\n',encoding='utf-8')
    env=os.environ.copy();env['MOON_HOME']=str(home)
    p=subprocess.run([str(moon),'run','.','--target','native'],cwd=directory,env=env,capture_output=True,timeout=180)
    evidence={'module':args.module,'version':args.version,'dependency':'registry only, no workspace/path override','directory':str(directory),'exit_code':p.returncode,'passed':p.returncode==0 and p.stdout.decode('utf-8').strip()=='unchanged'}
    (ROOT/'artifacts').mkdir(exist_ok=True)
    (ROOT/'artifacts/registry-consumer.log').write_bytes(p.stdout+p.stderr)
    (ROOT/'docs/registry-consumer-validation.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence))
    if not evidence['passed']:raise SystemExit(1)


if __name__=='__main__':main()

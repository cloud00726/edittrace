"""Regenerate public signatures and reject drift from the reviewed snapshots."""
import os
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
home=Path(os.environ.get('MOON_HOME',ROOT/'.tooling/moon')).resolve()
files=list(ROOT.glob('**/pkg.generated.mbti'))
files=[p for p in files if not any(part in ['_build','.mooncakes','.tooling','artifacts','output'] for part in p.relative_to(ROOT).parts)]
before={p:p.read_bytes() for p in files}
env=os.environ.copy();env['MOON_HOME']=str(home)
subprocess.run([str(home/'bin'/('moon.exe' if os.name=='nt' else 'moon')),'info'],cwd=ROOT,env=env,check=True)
changed=[str(p.relative_to(ROOT)) for p,b in before.items() if not p.exists() or p.read_bytes()!=b]
after=[p for p in ROOT.glob('**/pkg.generated.mbti') if not any(part in ['_build','.mooncakes','.tooling','artifacts','output'] for part in p.relative_to(ROOT).parts)]
changed.extend(str(p.relative_to(ROOT)) for p in after if p not in before)
if changed:raise SystemExit('Public API snapshots changed; review and regenerate explicitly: '+', '.join(changed))
print('Public API snapshots match the source.')

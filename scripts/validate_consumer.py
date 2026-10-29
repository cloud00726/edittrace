"""Compile/run the separate MoonBit consumer module using the local workspace."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    env=os.environ.copy()
    home=Path(env.get('MOON_HOME',ROOT/'.tooling/moon')).resolve()
    env['MOON_HOME']=str(home)
    moon=home/'bin'/('moon.exe' if os.name=='nt' else 'moon')
    backends=[]
    for target in ['native','js']:
        p=subprocess.run([str(moon),'run','.','--target',target],cwd=ROOT/'examples/consumer',env=env,capture_output=True,timeout=180)
        (ROOT/f'artifacts/consumer-{target}.log').write_bytes(p.stdout+p.stderr)
        backends.append({'target':target,'command':f'moon run . --target {target}','passed':p.returncode==0 and p.stdout.decode('utf-8').strip()=='A🌙C','output':p.stdout.decode('utf-8','replace'),'exit_code':p.returncode})
    passed=all(x['passed'] for x in backends)
    evidence={'passed':passed,'module':'local/edittrace_consumer','dependency':'local workspace, not published registry','backends':backends,'scope':'Pure edit/case/evidence consumer; share API invoked on native and JS; native CLI is not claimed to run on JS'}
    (ROOT/'docs/consumer-validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence))
    if not passed: raise SystemExit(1)

if __name__=='__main__':main()

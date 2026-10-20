"""Compile/run the separate MoonBit consumer module using the local workspace."""
import json, os, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    env=os.environ.copy()
    home=Path(env.get('MOON_HOME',ROOT/'.tooling/moon')).resolve()
    env['MOON_HOME']=str(home)
    moon=home/'bin'/('moon.exe' if os.name=='nt' else 'moon')
    p=subprocess.run([str(moon),'run','.','--target','native'],cwd=ROOT/'examples/consumer',env=env,capture_output=True,timeout=180)
    (ROOT/'artifacts/consumer.log').write_bytes(p.stdout+p.stderr)
    passed=p.returncode==0 and p.stdout.decode('utf-8').strip()=='A🌙C'
    evidence={'passed':passed,'module':'local/edittrace_consumer','dependency':'local workspace, not published registry','command':'moon run . --target native','output':p.stdout.decode('utf-8','replace'),'exit_code':p.returncode}
    (ROOT/'docs/consumer-validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence))
    if not passed: raise SystemExit(1)

if __name__=='__main__':main()

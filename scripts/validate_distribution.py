"""Check local artifacts; optionally install VSIX into an isolated VS Code profile."""
import argparse, hashlib, json, os, shutil, subprocess, tempfile, time, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from native_artifact import find_native_executable
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--directory',required=True);parser.add_argument('--install-vsix',action='store_true');args=parser.parse_args()
    folder=Path(args.directory).resolve(); manifest=json.loads((folder/'SHA256.json').read_text())
    checks=[]
    def check(name,truth):
        checks.append({'name':name,'passed':bool(truth)})
        if not truth:raise AssertionError(name)
    for name,digest in manifest['files'].items():
        check('archive hash '+name,hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest)
    work=Path(tempfile.mkdtemp(prefix='distribution with spaces ',dir=ROOT/'artifacts'))
    archive=next(folder.glob('*.zip')); vsix=next(folder.glob('*.vsix'))
    started=time.perf_counter()
    with zipfile.ZipFile(archive) as z:
        check('native ZIP CRC',z.testzip() is None);z.extractall(work)
    exe=work/('edittrace.exe' if os.name=='nt' else 'edittrace')
    if os.name!='nt':exe.chmod(0o755)
    check('native archive matches current build',exe.read_bytes()==find_native_executable(ROOT).read_bytes())
    for command in [['check-edits','examples/format.plan.json','--format','json'],['suite','run','examples/suite.json','--format','json']]:
        p=subprocess.run([str(exe),*command],cwd=work,capture_output=True,timeout=30)
        check('standalone '+' '.join(command[:2]),p.returncode==0 and json.loads(p.stdout)['exit_code']==0)
    p=subprocess.run([str(exe),'doctor','--format','json'],cwd=work,capture_output=True,timeout=30)
    check('standalone doctor matches candidate',p.returncode==0 and json.loads(p.stdout)['core_version']==manifest['core_version'])
    p=subprocess.run([str(exe),'suite','run','examples/suite.json','--format','junit'],cwd=work,capture_output=True,timeout=30)
    xml=ET.fromstring(p.stdout)
    check('standalone JUnit parsed independently',p.returncode==0 and xml.get('tests')=='4' and xml.get('errors')=='0')
    check('native ZIP contains licenses and provenance',all((work/name).is_file() for name in ['LICENSE','THIRD_PARTY_NOTICES.md','BUILD_INFO.json','licenses/MoonBit-core-LICENSE','licenses/moonbitlang-async-LICENSE']))
    elapsed=time.perf_counter()-started
    with zipfile.ZipFile(vsix) as z:
        check('VSIX CRC',z.testzip() is None)
        check('VSIX contains bundled native core',any(x.startswith('extension/bin/edittrace') for x in z.namelist()))
        check('VSIX contains manifest and documentation',all(x in z.namelist() for x in ['extension/package.json','extension/README.md','extension/LICENSE','extension.vsixmanifest','[Content_Types].xml']))
        check('VSIX contains every host module',all('extension/'+x in z.namelist() for x in ['diagnostics.js','presentation.js','project.js','BUILD_INFO.json']))
        check('VSIX/native share exact source provenance',json.loads(z.read('extension/BUILD_INFO.json'))==json.loads((work/'BUILD_INFO.json').read_text(encoding='utf-8')))
    install='not run';installed_extension=None
    if args.install_vsix:
        code=shutil.which('code')
        if not code:raise SystemExit('No VS Code; VSIX installation NOT verified')
        env=os.environ.copy();command=[code]
        if os.name=='nt':
            base=Path(code).parent.parent;cli=list(base.glob('*/resources/app/out/cli.js'))
            if len(cli)!=1:raise SystemExit('Cannot locate VS Code CLI')
            command=[str(base/'Code.exe'),str(cli[0])];env['ELECTRON_RUN_AS_NODE']='1'
        isolated=Path(tempfile.mkdtemp(prefix='vsix-install-',dir=ROOT/'.tooling'))
        p=subprocess.run([*command,'--install-extension',str(vsix),'--extensions-dir',str(isolated/'extensions'),'--user-data-dir',str(isolated/'profile'),'--force'],env=env,capture_output=True,timeout=120)
        (ROOT/'artifacts/vsix-install.log').write_bytes(p.stdout+p.stderr)
        installed=list((isolated/'extensions').glob('cloud00726.edittrace-*/package.json'))
        check('actual VS Code VSIX install',p.returncode==0 and len(installed)==1)
        check('installed binary matches package',hashlib.sha256((installed[0].parent/'bin'/exe.name).read_bytes()).hexdigest()==hashlib.sha256(exe.read_bytes()).hexdigest())
        installed_extension=str(installed[0].parent)
        install='installed into isolated profile; no Marketplace publish'
    evidence={'checks':checks,'passed':len(checks),'platform':manifest['platform'],'vsix_install':install,'installed_extension':installed_extension,'developer_extraction_and_first_report_seconds':elapsed,'measurement_scope':'local developer ZIP extraction and two commands; excludes download, install UI, human onboarding; not a five-minute user claim','published':False,'files':manifest['files']}
    (ROOT/'docs/distribution-validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(evidence,ensure_ascii=False))

if __name__=='__main__':main()

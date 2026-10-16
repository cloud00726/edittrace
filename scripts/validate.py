"""Native end-to-end acceptance. Python orchestrates checks; it does not audit traces."""
import argparse, hashlib, json, os, platform, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from make_examples import META,URI,CASES,opened,change,edit,checkpoint,msg,write_trace
from native_artifact import find_native_executable

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'artifacts'
ART.mkdir(exist_ok=True)
(ROOT/'docs').mkdir(exist_ok=True)
ENV=os.environ.copy()
if not ENV.get('MOON_HOME'):
    for p in [ROOT/'.tooling/moon',ROOT.parent/'tooling/moon']:
        if (p/'bin'/('moon.exe' if os.name=='nt' else 'moon')).exists(): ENV['MOON_HOME']=str(p);break
MOON=str(Path(ENV['MOON_HOME'])/'bin'/('moon.exe' if os.name=='nt' else 'moon')) if ENV.get('MOON_HOME') else shutil.which('moon')
EXE=None
results=[]

def run(args,cwd=ROOT):
    return subprocess.run(list(map(str,args)),cwd=cwd,env=ENV,capture_output=True,timeout=180)

def check(name,ok,detail=''):
    results.append(dict(name=name,passed=bool(ok),detail=detail))
    if not ok: raise AssertionError(name+': '+detail)

def tool(*args,expected=0):
    p=run([EXE,*args])
    check('CLI '+str(args[0])+' exit '+str(expected),p.returncode==expected,p.stderr.decode('utf-8','replace')[:500])
    return p

def audit(path,expected=0,*flags):
    p=tool('audit',path,'--format','json',*flags,expected=expected)
    j=json.loads(p.stdout)
    check('JSON/process exit agree',j['exit_code']==p.returncode)
    check('machine stdout only',not p.stderr)
    return j,p.stdout

def fixture(name,records):
    p=ART/(name+'.jsonl');write_trace(p,records);return p

def main():
    global EXE
    ap=argparse.ArgumentParser();ap.add_argument('--skip-build',action='store_true');ap.add_argument('--clean-room',action='store_true');a=ap.parse_args()
    if not a.skip_build:
        for args in [('fmt','--check'),('check','--target','native'),('test','--target','native'),('build','--target','native')]:
            p=run([MOON,*args]);(ART/('moon-'+args[0]+'.log')).write_bytes(p.stdout+p.stderr)
            check('moon '+' '.join(args),p.returncode==0,(p.stdout+p.stderr).decode('utf-8','replace')[-1400:])
    EXE=find_native_executable(ROOT)
    check('native executable exists',EXE.is_file())
    for name,(_,expected) in CASES.items():
        j,raw=audit(ROOT/'examples'/(name+'.jsonl'),expected)
        (ART/(name+'.report.json')).write_bytes(raw)
        j2,raw2=audit(ROOT/'examples'/(name+'.jsonl'),expected)
        check('deterministic '+name,raw==raw2)
    check('help',b'audit' in tool('--help').stdout)
    check('version',tool('--version').stdout==b'0.1.0\n')
    tool('not-a-command','x',expected=2)
    tool('audit',ROOT/'examples/valid-unicode.jsonl','--unknown','x',expected=2)
    tool('audit',ROOT/'examples/valid-unicode.jsonl','--format','xml',expected=2)
    out=Path(tempfile.mkdtemp(prefix='files with spaces ',dir=ART))
    text=out/'document.txt'
    p=tool('replay',ROOT/'examples/valid-unicode.jsonl','--uri',URI,'--at-seq','3','--out',text)
    check('exact UTF8 replay file',text.read_bytes()=='A🌙C\r\n你好'.encode())
    check('file mode stdout empty',p.stdout==b'')
    tool('replay',ROOT/'examples/valid-unicode.jsonl','--uri',URI,'--at-seq','3','--out',text,expected=2)
    tool('replay',ROOT/'examples/unknown-document.jsonl','--uri',URI,'--at-seq','1',expected=2)
    tool('replay',ROOT/'examples/valid-unicode.jsonl','--uri',URI,'--at-seq','99',expected=2)
    maximum=fixture('maximum-seq',[opened(2147483647)])
    audit(maximum,0)
    tool('replay',maximum,'--uri',URI,'--at-seq','2147483647')
    maximum.write_text(maximum.read_text(encoding='utf-8')+'{broken\n',encoding='utf-8')
    j,_=audit(maximum,2)
    check('audit validates suffix after maximum seq',j['input_error']['physical_line']==3)
    tool('replay',maximum,'--uri',URI,'--at-seq','2147483647')
    report,_=audit(ROOT/'examples/checkpoint-mismatch.jsonl',1)
    target=report['findings'][0]
    bundle=out/'repro'
    tool('export',ROOT/'examples/checkpoint-mismatch.jsonl','--finding',target['id'],'--out',bundle)
    check('bundle fixed files',sorted(p.name for p in bundle.iterdir())==['README.md','finding.json','manifest.json','trace.jsonl'])
    moved=out/'different location';shutil.copytree(bundle,moved)
    j,_=audit(moved/'trace.jsonl',1)
    check('relocated target fingerprint',target['fingerprint'] in [x['fingerprint'] for x in j['findings']])
    tool('export',ROOT/'examples/checkpoint-mismatch.jsonl','--finding',target['id'],'--out',bundle,expected=2)
    j,_=audit(ROOT/'examples/column-clamp.jsonl',0,'--fail-on','warning')
    check('clamp note threshold',j['counts']['notes']==1 and not j['counts']['warnings'])
    warning=fixture('warning-close',[msg(1,'didClose',dict(textDocument=dict(uri=URI)))])
    audit(warning,0);audit(warning,1,'--fail-on','warning')
    # Test every rule without depending on production-generated expectations.
    bad_cases=[
      ('duplicate-open',[opened(),opened(2,'second')],2,'ET002'),
      ('reversed',[opened(),change(2,[edit(0,2,0,1,'x')])],2,'ET005'),
      ('bad-line',[opened(),change(2,[edit(9,0,9,0,'x')])],2,'ET007'),
      ('checkpoint-version',[opened(),checkpoint(2,'abc',9)],0,'ET010'),
      ('wrong-direction',[opened(),msg(2,'didChange',dict(textDocument=dict(uri=URI,version=2),contentChanges=[dict(text='x')]),'server_to_client')],1,'ET011'),
      ('range-length',[opened(),change(2,[edit(0,0,0,1,'X',rangeLength=9)])],0,'ET012'),
      ('state-unknown',[opened(text='🌙'),change(2,[edit(0,1,0,1,'x')]),change(3,[edit(0,0,0,0,'y')],3)],2,'ET013'),
      ('empty-changes',[opened(),change(2,[])],2,'ET014'),
      ('checkpoint-available-after-close',[opened(),msg(2,'didClose',dict(textDocument=dict(uri=URI))),checkpoint(3,'abc',1)],0,'ET010'),
    ]
    for name,records,expected,rule in bad_cases:
        j,_=audit(fixture(name,records),expected)
        check('rule '+rule,any(f['rule_id'].startswith(rule) for f in j['findings']))
    invalids=[
      ('null-range',[opened(),change(2,[dict(range=None,text='x')])]),
      ('fraction-version',[opened(version=1.5)]),
      ('overflow-version',[opened(version=2147483648)]),
      ('negative-position',[opened(),change(2,[edit(0,-1,0,0,'x')])]),
      ('missing-source',[opened(),{k:v for k,v in checkpoint(2,'abc',1).items() if k!='source'}]),
      ('duplicate-seq',[opened(),checkpoint(1,'abc',1)]),
      ('unknown-kind',[dict(kind='other',seq=1)]),
    ]
    for name,records in invalids:
        j,_=audit(fixture(name,records),2);check('invalid incomplete '+name,not j['analysis_complete'])
    for name,data in [('invalid-json',b'{bad\n'),('invalid-utf8',b'\xff\n'),('empty',b'')]:
        p=ART/(name+'.jsonl');p.write_bytes(data);audit(p,2)
    for name,key,val in [('encoding','position_encoding','utf-8'),('schema','schema_version',2)]:
        p=ART/(name+'.jsonl');p.write_text(json.dumps(dict(META,**{key:val}))+'\n',encoding='utf-8');audit(p,2)
    for flag,value,records in [
      ('--max-record-bytes','32',[opened()]),('--max-input-bytes','32',[opened()]),
      ('--max-document-bytes','2',[opened(text='你好')]),
      ('--max-open-documents','1',[opened(),opened(2,'b',1,'file:///second')]),
      ('--max-findings','1',[change(1,[dict(text='x')]),change(2,[dict(text='y')],3)]),
    ]:
        j,_=audit(fixture('limit-'+flag[6:],records),2,flag,value)
        check('resource reason '+flag,j['input_error'] is not None)
    deep=ART/'deep-json.jsonl';deep.write_text(json.dumps(META)+'\n'+ '['*100+'0'+']'*100+'\n',encoding='utf-8');audit(deep,2)
    crlf=ART/'bom-crlf.jsonl';crlf.write_bytes(b'\xef\xbb\xbf'+(ROOT/'examples/valid-sequential.jsonl').read_bytes().replace(b'\n',b'\r\n'));audit(crlf,0)
    # Stable independent corpus checksum, plus a CLI sample from its final sequence.
    manifest=json.loads((ROOT/'tests/oracle/manifest.json').read_text())
    corpus=(ROOT/'tests/oracle/corpus.jsonl').read_bytes()
    check('oracle corpus digest',hashlib.sha256(corpus).hexdigest()==manifest['corpus_sha256'])
    oracle=ART/'oracle-cli-sample.jsonl';oracle.write_text(json.loads(corpus.splitlines()[-1]),encoding='utf-8');j,_=audit(oracle)
    check('oracle CLI checkpoints',j['counts']['checkpoints_passed']==8)
    # Actual timings; no pass/fail promise or invented memory measurements.
    bench=ART/'bench-10000.jsonl'
    records=[opened(text='x'*1048576),opened(2,'x'*1000,1,'file:///small-a'),opened(3,'x'*1000,1,'file:///small-b')]
    records.extend(change(i+4,[edit(0,i%1000,0,i%1000+1,'x')],i+2,'file:///small-a' if i%2==0 else 'file:///small-b') for i in range(10000))
    write_trace(bench,records)
    # Total input stays below the documented 64 MiB limit.
    start=time.perf_counter();p=run([EXE,'audit',bench,'--format','json']);elapsed=time.perf_counter()-start
    check('benchmark completes',p.returncode==0)
    benchmark=dict(records=10003,documents=3,large_document_bytes=1048576,small_edits=10000,input_bytes=bench.stat().st_size,elapsed_seconds=elapsed,memory='not measured',os=platform.platform(),processor=platform.processor())
    (ART/'benchmark.json').write_text(json.dumps(benchmark,indent=2)+'\n',encoding='utf-8')
    if a.clean_room:
        clean=Path(tempfile.mkdtemp(prefix='clean-room-',dir=ART))/'source'
        shutil.copytree(ROOT,clean,ignore=shutil.ignore_patterns('_build','.mooncakes','artifacts','.tooling','node_modules','.git','*.log','__pycache__'))
        p=run([MOON,'build','--target','native'],cwd=clean);check('clean-room build',p.returncode==0,(p.stdout+p.stderr).decode('utf-8','replace')[-500:])
        clean_exe=find_native_executable(clean)
        p=run([clean_exe,'audit','examples/valid-unicode.jsonl','--format','json'],cwd=clean)
        check('clean-room README example',p.returncode==0 and json.loads(p.stdout)['counts']['checkpoints_passed']==1)
    versions=run([MOON,'version','--all']).stdout.decode('utf-8','replace')
    evidence=dict(passed=sum(x['passed'] for x in results),checks=results,platform=platform.platform(),toolchain=versions,oracle=manifest,benchmark=benchmark,clean_room=a.clean_room)
    (ROOT/'docs'/'validation-results.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(passed=evidence['passed'],oracle_sequences=500,oracle_checkpoints=4000,clean_room=a.clean_room,benchmark_seconds=elapsed)))

if __name__=='__main__':
    try: main()
    except Exception as exc:
        (ART/'validation-failure.json').write_text(json.dumps(dict(error=str(exc),checks=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        raise

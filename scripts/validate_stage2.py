"""Independent CLI checks for stage2. No production transformation in Python."""
import argparse, copy, hashlib, json, os, shutil, subprocess, tempfile, zipfile
from pathlib import Path
from native_artifact import find_native_executable
ROOT=Path(__file__).resolve().parents[1]

def legacy(exe):
    archives={
      '0.1.0':ROOT/'output/release/edittrace-core-0.1.0-win32-x64.zip',
      '0.2.0':ROOT/'output/remote-run-39429451845/evidence-windows-latest/output/release/edittrace-core-0.2.0-win32-x64.zip',
      '0.3.0':ROOT/'output/maintenance-0.3.0-20261025-final/edittrace-core-0.3.0-win32-x64.zip'}
    results=[]
    base=Path(tempfile.mkdtemp(prefix='legacy-real-',dir=ROOT/'artifacts'))
    for version,archive in archives.items():
        if os.name!='nt' or not archive.is_file():
            results.append({'version':version,'status':'unavailable','reason':'real legacy platform artifact not present'});continue
        folder=base/version;folder.mkdir()
        with zipfile.ZipFile(archive) as z:(folder/'old.exe').write_bytes(z.read('edittrace.exe'))
        old=folder/'old.exe'
        actual=subprocess.check_output([old,'--version']).decode().strip()
        assert actual==version,(actual,version)
        bundle=folder/'bundle'
        p=subprocess.run([old,'export',ROOT/'examples/checkpoint-mismatch.jsonl','--finding','ET009_CHECKPOINT_MISMATCH:3:-1:0','--out',bundle],capture_output=True,timeout=30)
        assert p.returncode==0,p.stderr
        p=subprocess.run([exe,'verify',bundle],capture_output=True,timeout=30)
        results.append({'version':version,'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'verify_exit':p.returncode,'real_producer':True})
    return results

def validate(exe,root=ROOT):
    checks=[]
    def check(name,ok):
        checks.append({'name':name,'passed':bool(ok)})
        if not ok:raise AssertionError(name)
    def run(*args,expected=0):
        p=subprocess.run([str(exe),*map(str,args)],cwd=root,capture_output=True,timeout=30)
        if p.returncode!=expected:raise AssertionError((args,p.returncode,p.stderr.decode('utf-8','replace')))
        return p
    with tempfile.TemporaryDirectory(prefix='stage2-',dir=root/'artifacts') as t:
        t=Path(t);trace=t/'source.jsonl'
        records=[json.loads(s) for s in (root/'examples/checkpoint-mismatch.jsonl').read_text(encoding='utf-8').splitlines()]
        identity='file:///private-user/秘密.mbt'
        for rec in records:
            if rec['kind']=='checkpoint':rec['uri']=identity
            if rec['kind']=='message':rec['message']['params']['textDocument']['uri']=identity
        # An explicitly redundant text update gives minimization a meaningful deletion.
        noop={'kind':'message','seq':2,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didChange','params':{'textDocument':{'uri':identity,'version':2},'contentChanges':[{'text':'🌙ab'}]}}}
        records.insert(2,noop)
        records[3]['seq']=3;records[3]['message']['params']['textDocument']['version']=3
        records[4]['seq']=4;records[4]['version']=3
        def write(value):trace.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in value)+'\n',encoding='utf-8')
        write(records);original=trace.read_bytes();id='ET009_CHECKPOINT_MISMATCH:4:-1:0'
        p=run('share','plan',trace,'--finding',id)
        check('preview excludes original identity and source',identity.encode() not in p.stdout and '🌙ab'.encode() not in p.stdout)
        check('preview deterministic and read-only',run('share','plan',trace,'--finding',id).stdout==p.stdout and trace.read_bytes()==original)
        shared=t/'share';run('share','export',trace,'--finding',id,'--out',shared)
        check('sharing independently verifies',json.loads(run('evidence','verify',shared).stdout)['verified'])
        transformed=[json.loads(l) for l in (shared/'trace.jsonl').read_text(encoding='utf-8').splitlines() if l]
        check('structured identities removed from every shared file',all(identity not in f.read_text(encoding='utf-8') for f in shared.iterdir() if f.is_file()))
        def texts(rs):
            values=[]
            for r in rs:
                if r['kind']=='checkpoint':values.append(r['text'])
                if r['kind']=='message':
                    doc=r['message']['params']['textDocument']
                    if 'text'in doc:values.append(doc['text'])
                    values.extend(c['text'] for c in r['message']['params'].get('contentChanges',[]))
            return values
        check('source text and Unicode preserved exactly',texts(records)==texts(transformed))
        moved=t/'moved';shutil.copytree(shared,moved);run('evidence','verify',moved)
        check('shared package relocates',True)
        for name in ['trace.jsonl','finding.json','manifest.json','receipt.json']:
            altered=t/('bad-'+name.replace('.','-'));shutil.copytree(shared,altered)
            file=altered/name
            if name=='trace.jsonl':file.write_text(file.read_text(encoding='utf-8')+'\n',encoding='utf-8')
            else:
                v=json.loads(file.read_text(encoding='utf-8'));v['unexpected']='tampered';file.write_text(json.dumps(v),encoding='utf-8')
            run('evidence','verify',altered,expected=2);check('tampering rejected '+name,True)
        run('share','export',trace,'--finding',id,'--out',shared,expected=2);check('exclusive share output',True)
        run('share','plan',trace,'--finding','missing',expected=2);check('unknown target rejected',True)
        bad=copy.deepcopy(records);bad[1]['message']['params']['hidden']='secret';write(bad)
        run('share','plan',trace,'--finding',id,expected=2);check('unknown sharing fields rejected',True)
        write(records)
        minimized=t/'small';stats=json.loads(run('minimize',trace,'--finding',id,'--out',minimized).stdout)
        check('redundant change removed',stats['accepted']>=1 and stats['retained_nonblank']<stats['original_nonblank'])
        run('evidence','verify',minimized)
        original_finding=json.loads(run('audit',trace,'--format','json',expected=1).stdout)['findings'][0]
        replay=json.loads(run('audit',minimized/'trace.jsonl','--format','json',expected=1).stdout)
        check('final candidate preserves complete target finding',original_finding in replay['findings'])
        check('physical line mapping retained',len((minimized/'trace.jsonl').read_text(encoding='utf-8').splitlines())==len(records))
        limited=json.loads(run('minimize',trace,'--finding',id,'--max-runs','1','--out',t/'limited').stdout)
        check('replay budget respected',limited['attempts']<=1 and limited['budget_exhausted'])
        run('minimize',trace,'--finding',id,'--max-runs','0','--out',t/'zero',expected=2)
        check('invalid budget rejected',True)
        multi=copy.deepcopy(records);multi.append({'kind':'message','seq':5,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didOpen','params':{'textDocument':{'uri':'file:///second','version':1,'text':'hello','languageId':'text'}}}})
        write(multi);run('minimize',trace,'--finding',id,'--out',t/'multi',expected=2);check('multi-document minimize rejected',True)
        run('share','export',trace,'--finding',id,'--out',t/'multi-share');run('evidence','verify',t/'multi-share');check('multi-document share supported',True)
        write(records);trace.write_bytes(original+b'{broken\n')
        run('minimize',trace,'--finding',id,'--out',t/'broken',expected=2);check('malformed suffix cannot substitute target',True)
        # Actual source identity in a code literal is intentionally retained and disclosed.
        literals=copy.deepcopy(records);literals[1]['message']['params']['textDocument']['text']+=identity
        write(literals)
        r=run('share','plan',trace,'--finding',id)
        check('retained literals explicitly disclosed',json.loads(r.stdout)['source_text_retained'])
        write(records)
        locked=copy.deepcopy(records);locked.pop(2);locked[2]['seq']=2;locked[2]['message']['params']['textDocument']['version']=2;locked[3]['seq']=3;locked[3]['version']=2
        write(locked)
        nochange=json.loads(run('minimize',trace,'--finding','ET009_CHECKPOINT_MISMATCH:3:-1:0','--out',t/'no-change').stdout)
        check('non-reducible trace is reported honestly',nochange['accepted']==0)
        generation=copy.deepcopy(locked)
        generation.insert(1,{'kind':'message','seq':1,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didOpen','params':{'textDocument':{'uri':identity,'version':1,'text':'old generation','languageId':'text'}}}})
        generation.insert(2,{'kind':'message','seq':2,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didClose','params':{'textDocument':{'uri':identity}}}})
        for i,r in enumerate(generation[1:],1):r['seq']=i
        write(generation);genid='ET009_CHECKPOINT_MISMATCH:5:-1:0'
        run('minimize',trace,'--finding',genid,'--out',t/'generation');run('evidence','verify',t/'generation')
        check('reopened generation and checkpoint identity preserved',True)
        run('minimize',trace,'--finding','ET009_CHECKPOINT_MISMATCH:999:-1:0','--out',t/'missing',expected=2);check('minimize missing target rejected',True)
        # Exercise the evidence-specific guards, not only the general audit reader.
        write(records);trace.write_bytes(trace.read_bytes()+b'\n'*2048)
        run('share','plan',trace,'--finding',id,expected=2);check('evidence physical line bound enforced',True)
        trace.write_bytes(b' '*8388609)
        run('share','plan',trace,'--finding',id,expected=2);check('evidence byte bound enforced',True)
        write(records);trace.write_bytes(trace.read_bytes()+b'\xff\n')
        run('share','plan',trace,'--finding',id,expected=2);check('evidence invalid UTF-8 rejected',True)
        controls=copy.deepcopy(records)
        for rec in controls:
            if rec['kind']=='checkpoint':rec['uri']='file:///private\tcontrol\nname'
            if rec['kind']=='message':rec['message']['params']['textDocument']['uri']='file:///private\tcontrol\nname'
        write(controls);run('share','export',trace,'--finding',id,'--out',t/'controls');run('evidence','verify',t/'controls')
        check('control characters in identity map without corrupting source',True)
        unsupported=copy.deepcopy(records)
        unsupported[3]['message']['params']['contentChanges'][0]['range']['end']['character']=999
        write(unsupported)
        report=json.loads(run('audit',trace,'--format','json',expected=1).stdout)
        other=next(f['id'] for f in report['findings'] if f['rule_id']!='ET009_CHECKPOINT_MISMATCH')
        run('minimize',trace,'--finding',other,'--out',t/'unsupported',expected=2)
        check('present but unsupported target rule rejected',True)
    evidence={'passed':len(checks),'checks':checks,'scope':'independent CLI replay, mutation, relocation and preservation checks'}
    (root/'docs/stage2-validation.json').write_text(json.dumps(evidence,indent=2)+'\n',encoding='utf-8')
    return evidence

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--legacy-only',action='store_true');args=parser.parse_args()
    if args.legacy_only:
        values=legacy(find_native_executable(ROOT));(ROOT/'artifacts/legacy-stage2.json').write_text(json.dumps(values,indent=2)+'\n',encoding='utf-8')
        (ROOT/'docs/stage2-legacy-validation.json').write_text(json.dumps({'baseline_validator':'0.3.0 at 5ed61ab','observed_before_fix':{'0.1.0':0,'0.2.0':2,'0.3.0':0},'after_fix':values},indent=2)+'\n',encoding='utf-8')
        if any(x.get('verify_exit',0)!=0 for x in values):raise SystemExit('A real available legacy bundle failed')
        print(json.dumps(values))
    else:print(json.dumps(validate(find_native_executable(ROOT))))

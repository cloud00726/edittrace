"""Behavior checks for import, edit preflight, portable cases and batch execution."""
import copy, json, os, shutil, subprocess, tempfile
from pathlib import Path
from native_artifact import find_native_executable

ROOT = Path(__file__).resolve().parents[1]

def validate(exe=None, root=ROOT):
    root=Path(root); exe=Path(exe or find_native_executable(root)); checks=[]
    directory=Path(tempfile.mkdtemp(prefix='remediation with spaces ',dir=root/'artifacts'))
    def check(name,truth):
        checks.append({'name':name,'passed':bool(truth)})
        if not truth: raise AssertionError(name)
    def run(*args, expected=0):
        p=subprocess.run([str(exe),*map(str,args)],capture_output=True,timeout=30)
        check(' '.join(map(str,args[:2]))+' exit '+str(expected),p.returncode==expected)
        if p.stdout and args[0]!='import':
            j=json.loads(p.stdout)
            check('report/process status agree',j['exit_code']==expected)
            return j
        return p
    counter=0
    def fixture(value):
        nonlocal counter
        counter+=1; file=directory/(str(counter)+'.json')
        file.write_text(json.dumps(value,ensure_ascii=False),encoding='utf-8'); return file
    for args in [['case','run','--help'],['case','create','--help'],['suite','run','--help']]:
        p=subprocess.run([str(exe),*args],capture_output=True,timeout=30)
        check('nested command help '+' '.join(args[:2]),p.returncode==0 and b'--out' in p.stdout)
    real=root/'examples/real-world'
    for name in ['format','rename']:
        report=run('check-edits',real/(name+'.plan.json'),'--format','json')
        check('actual independent host text compared '+name,all(d['actual_compared'] for d in report['documents']))
    suite=run('suite','run',real/'suite.json','--format','json')
    check('three real tasks and fault-reproduction case',len(suite['cases'])==4 and all(x['passed'] for x in suite['cases']))
    lost=run('case','run',real/'injected-lost-event.case.json','--format','json',expected=1)
    check('lost event cannot pass recorded independent text assertions',not lost['passed'])
    imported=directory/'imported.jsonl'
    run('import',real/'vscode-jsonrpc.jsonl','--from','vscode-json','--out',imported)
    audited=run('audit',imported,'--format','json')
    check('real server trace imported with no invented checkpoints',audited['counts']['checkpoints_passed']==0 and audited['meta']['encoding_basis']=='initialize_default_utf16')
    run('import',real/'vscode-jsonrpc.jsonl','--from','vscode-json','--out',imported,expected=2)
    logs=[json.loads(s) for s in (real/'vscode-jsonrpc.jsonl').read_text(encoding='utf-8').splitlines()]
    for name, mutate in [
        ('bad-type',lambda x:x[0].update(type='mystery')),
        ('type-shape-mismatch',lambda x:x[0].update(type='receive-response')),
        ('unsupported-encoding',lambda x:next(j for j in x if j['type']=='receive-response')['message']['result']['capabilities'].update(positionEncoding='utf-8')),
        ('mixed-session',lambda x:x.append(copy.deepcopy(x[0]))),
    ]:
        modified=copy.deepcopy(logs);mutate(modified)
        file=directory/(name+'.jsonl');file.write_text(''.join(json.dumps(j)+'\n' for j in modified),encoding='utf-8')
        dest=directory/(name+'.out')
        run('import',file,'--from','vscode-json','--out',dest,expected=2)
        check('invalid import not promoted '+name,not dest.exists())
    truncated=directory/'truncated.jsonl';truncated.write_text(json.dumps(logs[0])+'\n{"type":',encoding='utf-8')
    run('import',truncated,'--from','vscode-json','--out',directory/'truncated.out',expected=2)
    reused=copy.deepcopy(logs)
    request=next(j for j in reused if j['type']=='send-request' and j['message'].get('method')=='textDocument/formatting')
    old_id=request['message']['id'];request['message']['id']=logs[0]['message']['id']
    next(j for j in reused if j['type']=='receive-response' and j['message'].get('id')==old_id)['message']['id']=request['message']['id']
    file=directory/'reused-id.jsonl';file.write_text(''.join(json.dumps(j)+'\n' for j in reused),encoding='utf-8')
    run('import',file,'--from','vscode-json','--out',directory/'reused-id.out')
    base=json.loads((real/'format.plan.json').read_text(encoding='utf-8'))
    mismatch=copy.deepcopy(base);mismatch['actual'][0]['text']='WRONG'
    report=run('check-edits',fixture(mismatch),'--format','json',expected=1)
    check('mismatch contains actionable evidence',report['findings'][0]['rule_id']=='EP003_ACTUAL_MISMATCH' and 'first_difference_utf16' in report['findings'][0])
    stale=copy.deepcopy(base);stale['workspace_edit']['documentChanges'][0]['textDocument']['version']+=1
    report=run('check-edits',fixture(stale),'--format','json',expected=1)
    check('stale version is preflight failure',report['findings'][0]['rule_id']=='EP001_VERSION_MISMATCH')
    malformed=copy.deepcopy(stale);malformed['workspace_edit']['documentChanges'][0]['edits']='invalid'
    run('check-edits',fixture(malformed),'--format','json',expected=2)
    malformed=copy.deepcopy(stale);malformed['actual'][0]['uri']='file:///wrong'
    run('check-edits',fixture(malformed),'--format','json',expected=2)
    same=copy.deepcopy(base);op=same['workspace_edit']['documentChanges'][0];overlap={'range':{'start':{'line':0,'character':0},'end':{'line':0,'character':2}},'newText':'x'};op['edits']=[overlap,overlap]
    report=run('check-edits',fixture(same),'--format','json',expected=1)
    check('overlap rejected',report['findings'][0]['rule_id']=='EP002_OVERLAPPING_EDITS')
    for name,mutate in [
        ('missing-baseline',lambda p:p.update(documents=[])),
        ('resource-operation',lambda p:p['workspace_edit']['documentChanges'].append({'kind':'create','uri':'file:///x'})),
        ('annotated-edit',lambda p:p['workspace_edit']['documentChanges'][0]['edits'][0].update(annotationId='x')),
        ('duplicate-operation',lambda p:p['workspace_edit']['documentChanges'].append(copy.deepcopy(p['workspace_edit']['documentChanges'][0]))),
        ('missing-actual',lambda p:p.update(actual=[])),
        ('wrong-actual-uri',lambda p:p['actual'][0].update(uri='file:///wrong')),
        ('non-utf16',lambda p:p.update(position_encoding='utf-8')),
        ('fraction-version',lambda p:p['documents'][0].update(version=1.5)),
        ('surrogate-boundary',lambda p:p['workspace_edit']['documentChanges'][0].update(edits=[{'range':{'start':{'line':0,'character':10},'end':{'line':0,'character':10}},'newText':'x'}])),
    ]:
        modified=copy.deepcopy(base);mutate(modified)
        run('check-edits',fixture(modified),'--format','json',expected=2)
    unconstrained=copy.deepcopy(base);op=unconstrained['workspace_edit'].pop('documentChanges')[0]
    unconstrained['workspace_edit']['changes']={op['textDocument']['uri']:op['edits']}
    report=run('check-edits',fixture(unconstrained),'--format','json')
    check('unversioned changes explicitly unverified',report['documents'][0]['version_checked'] is False)
    case=json.loads((real/'format.case.json').read_text(encoding='utf-8'))
    wrong=copy.deepcopy(case);wrong['expect']['texts'][0]['text']='wrong'
    run('case','run',fixture(wrong),'--format','json',expected=1)
    typo=copy.deepcopy(case);typo['expect']['textz']=[]
    report=run('case','run',fixture(typo),'--format','json',expected=2)
    check('unknown expectation cannot silently pass',report['analysis_complete'] is False)
    invalid_step=copy.deepcopy(case);invalid_step['expect']['texts'][0]['at_seq']=0
    run('case','run',fixture(invalid_step),'--format','json',expected=2)
    mixed={'kind':'suite','schema_version':1,'cases':[typo,case]}
    report=run('suite','run',fixture(mixed),'--format','json',expected=2)
    check('invalid case does not suppress later cases',len(report['cases'])==2 and report['cases'][1]['passed'])
    # A long capture with step assertions is evaluated in one replay, not N replays.
    uri='file:///linear-replay';records=[{'kind':'meta','schema_version':1,'position_encoding':'utf-16','capture_mode':'fragment','provenance':'synthetic','producer':'review-regression'}, {'kind':'message','seq':1,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didOpen','params':{'textDocument':{'uri':uri,'version':1,'languageId':'test','text':'0'}}}}]
    texts=[]
    for i in range(2,1502):
        records.append({'kind':'message','seq':i,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':'textDocument/didChange','params':{'textDocument':{'uri':uri,'version':i},'contentChanges':[{'text':str(i)}]}}})
        texts.append({'uri':uri,'at_seq':i,'text':str(i)})
    run('case','run',fixture({'kind':'case','schema_version':1,'name':'long-step-capture','source':{'kind':'synthetic_regression'},'input':{'kind':'trace','records':records},'expect':{'exit_code':0,'analysis_complete':True,'texts':texts}}),'--format','json')
    package=directory/'new case'
    run('case','create',real/'format.case.json','--out',package)
    relocated=directory/'relocated';shutil.copytree(package,relocated)
    run('case','run',relocated/'case.json','--format','json')
    run('case','create',real/'format.case.json','--out',package,expected=2)
    run('case','create',fixture(wrong),'--out',directory/'bad case',expected=2)
    check('failing expectations do not become verified package',not (directory/'bad case').exists())
    records=[json.loads(s) for s in (real/'sync.jsonl').read_text(encoding='utf-8').splitlines()]
    checkpoint=copy.deepcopy(next(r for r in reversed(records) if r.get('kind')=='checkpoint' and r['uri'].endswith('events.txt')))
    checkpoint.update(seq=records[-1]['seq']+1,text='injected mismatch',source='fault_injection')
    records.append(checkpoint)
    trace=directory/'multi-document-fault.jsonl';trace.write_text(''.join(json.dumps(r)+'\n' for r in records),encoding='utf-8')
    report=run('audit',trace,'--format','json',expected=1)
    target=report['findings'][-1];filtered=directory/'filtered'
    p=subprocess.run([str(exe),'export',str(trace),'--finding',target['id'],'--uri',checkpoint['uri'],'--out',str(filtered)],capture_output=True,timeout=30)
    check('document-filtered export revalidates target',p.returncode==0 and json.loads(p.stdout)['strategy']=='document_prefix_preserving_lines')
    p=subprocess.run([str(exe),'verify',str(filtered)],capture_output=True,timeout=30)
    check('filtered package independently verifies',p.returncode==0 and json.loads(p.stdout)['verified'])
    legacy=directory/'legacy-bundle';shutil.copytree(filtered,legacy)
    old_manifest=json.loads((legacy/'manifest.json').read_text(encoding='utf-8'));old_manifest['tool_version']='0.1.0'
    (legacy/'manifest.json').write_text(json.dumps(old_manifest),encoding='utf-8')
    p=subprocess.run([str(exe),'verify',str(legacy)],capture_output=True,timeout=30)
    check('legacy 0.1 bundle remains verifiable',p.returncode==0)
    check('unrelated document text removed',b'second.txt' not in (filtered/'trace.jsonl').read_bytes())
    manifest=json.loads((filtered/'manifest.json').read_text(encoding='utf-8'));manifest['filter_uri']='file:///wrong'
    (filtered/'manifest.json').write_text(json.dumps(manifest),encoding='utf-8')
    p=subprocess.run([str(exe),'verify',str(filtered)],capture_output=True,timeout=30)
    check('tampered filter scope fails verification',p.returncode==2)
    p=subprocess.run([str(exe),'check-edits',str(real/'format.plan.json')],capture_output=True,timeout=30)
    check('human report avoids dumping entire source',p.returncode==0 and b'actual compared=true' in p.stdout and b'items' not in p.stdout)
    evidence={'passed':len(checks),'checks':checks,'scope':'CLI behavior with committed actual-host fixtures; does not rerun live host or measure human demand'}
    (root/'docs/remediation-validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return evidence

if __name__=='__main__':
    result=validate();print(json.dumps({'passed':result['passed']}))

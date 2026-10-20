"""Normalize only URI identifiers in real host captures; keep actual text/edits intact."""
import copy, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    raw = ROOT/'artifacts/vscode-host/result.json'
    report = json.loads(raw.read_text(encoding='utf-8'))
    if report.get('error') or not report.get('checks') or not all(c['passed'] for c in report['checks']):
        raise SystemExit('Only a successful actual host result can produce captured examples')
    out = ROOT/'examples/real-world'
    out.mkdir(parents=True, exist_ok=True)
    uris = set()
    def collect(value):
        if isinstance(value, dict):
            for k,v in value.items():
                if k == 'uri' and isinstance(v,str): uris.add(v)
                collect(v)
        elif isinstance(value,list):
            for v in value: collect(v)
    collect(report['samples'])
    mapping = {u:'file:///edittrace-demo/'+u.rsplit('/',1)[-1] for u in uris}
    if len(set(mapping.values())) != len(mapping): raise SystemExit('URI normalization collision')
    def normalize(v):
        if isinstance(v,dict): return {k:normalize(x) for k,x in v.items()}
        if isinstance(v,list): return [normalize(x) for x in v]
        return mapping.get(v,v) if isinstance(v,str) else v
    samples = normalize(report['samples'])
    def write(name,value): (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    cases=[]
    if 'same_position' in samples:write('same-position.plan.json',samples['same_position'])
    if 'same_position_events' in samples:
        uri=samples['same_position']['documents'][0]['uri']
        records=[r for r in samples['same_position_events'] if r['kind']=='meta' or r.get('uri')==uri or r.get('message',{}).get('params',{}).get('textDocument',{}).get('uri')==uri]
        checkpoint=next(r for r in records if r['kind']=='checkpoint')
        write('same-position-events.case.json',{'schema_version':1,'kind':'case','name':'real-host-same-position-events','source':{'kind':'captured_document_filtered','host':report['host']},'input':{'kind':'trace','records':records},'expect':{'analysis_complete':True,'exit_code':0,'texts':[{'uri':uri,'text':checkpoint['text'],'at_seq':checkpoint['seq']}]}})
    for name in ['format','rename']:
        plan=samples[name]
        write(name+'.plan.json',plan)
        case={'schema_version':1,'kind':'case','name':'real-host-'+name,'source':{'kind':'captured','host':report['host'],'task':name},'input':{'kind':'edit_plan','plan':plan},'expect':{'exit_code':0,'analysis_complete':True,'texts':copy.deepcopy(plan['actual'])}}
        write(name+'.case.json',case);cases.append(case)
    (out/'sync.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in samples['sync']),encoding='utf-8')
    sync={'schema_version':1,'kind':'case','name':'real-host-sync','source':{'kind':'captured','host':report['host']},'input':{'kind':'trace','records':samples['sync']},'expect':{'exit_code':0,'analysis_complete':True,'texts':[{'uri':r['uri'],'text':r['text'],'at_seq':r['seq']} for r in samples['sync'] if r['kind']=='checkpoint']}}
    write('sync.case.json',sync);cases.append(sync)
    stale=copy.deepcopy(cases[0]);stale['name']='injected-stale-version';stale['source']['kind']='fault_injection_on_real_capture'
    stale['input']['plan']['workspace_edit']['documentChanges'][0]['textDocument']['version']+=1
    stale['expect']={'exit_code':1,'analysis_complete':True,'findings':[{'rule_id':'EP001_VERSION_MISMATCH'}]}
    write('injected-stale.case.json',stale);cases.append(stale)
    missing=copy.deepcopy(sync);missing['name']='injected-lost-event';missing['source']['kind']='fault_injection_on_real_capture'
    records=missing['input']['records'];index=next(i for i,r in enumerate(records) if r.get('message',{}).get('method')=='textDocument/didChange');records.pop(index)
    missing['expect']={'exit_code':0,'analysis_complete':True,'texts':sync['expect']['texts']}
    # Deliberately failing regression: lost edit cannot reproduce independently observed snapshot.
    write('injected-lost-event.case.json',missing)
    write('suite.json',{'schema_version':1,'kind':'suite','cases':cases})
    trace=ROOT/'artifacts/real-jsonrpc.jsonl'
    if trace.exists(): (out/'vscode-jsonrpc.jsonl').write_bytes(trace.read_bytes())
    write('capture-evidence.json',{'capture_date':'2026-10-20','host':report['host'],'extension_mode':report.get('extension_mode','source'),'providers':report['providers'],'checks':report['checks'],'host_result_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'normalization':'URI identifiers replaced with stable file:///edittrace-demo/<name>; edit ranges, versions and independent actual text unchanged','jsonrpc':'vscode-jsonrpc@8.2.1 against installed Microsoft JSON server; not arbitrary third-party extension interception','human_trial':False})
    print(json.dumps({'cases':len(cases),'host_checks':len(report['checks'])}))

if __name__=='__main__':main()

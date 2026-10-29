"""Reproducible development measurements; no correctness logic is implemented here."""
import argparse, ctypes, hashlib, json, os, platform, statistics, subprocess, time
from pathlib import Path
from native_artifact import find_native_executable
ROOT=Path(__file__).resolve().parents[1]

def peak_memory(process):
    if os.name!='nt':return {'metric':'unavailable','reason':'per-process peak measurement not implemented for this platform'}
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)]+[(n,ctypes.c_size_t) for n in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
    values=Counters();values.cb=ctypes.sizeof(values)
    query=ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes=[wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD];query.restype=wintypes.BOOL
    if not query(wintypes.HANDLE(int(process._handle)),ctypes.byref(values),values.cb):return {'metric':'unavailable','reason':'GetProcessMemoryInfo failed','winerror':ctypes.get_last_error()}
    return {'metric':'Windows PeakWorkingSetSize','bytes':values.PeakWorkingSetSize,'scope':'native child process, queried after completion while process handle remains open'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--quick',action='store_true');ap.add_argument('--out',required=True);a=ap.parse_args()
    out=Path(a.out).resolve();out.mkdir(parents=True,exist_ok=False)
    exe=find_native_executable(ROOT)
    scenarios=[(10240,100,'unicode-crlf'),(102400,1000,'multi-document')]
    if not a.quick:scenarios += [(1048576,100,'long-line'),(10240,10000,'incremental'),(102400,100,'full-replace'),(1048576,1,'batch-textedit')]
    results=[]
    for size,count,mode in scenarios:
        baseline=('🌙中文\r\n'+'x'*64)*(size//80+1)
        baseline=baseline[:size//2] if mode!='long-line' else 'x'*size
        baseline=baseline+'x'*max(0,size-len(baseline.encode('utf-8')))
        uri='file:///benchmark.mbt';target=out/(mode+'.json')
        if mode=='batch-textedit':
            plan={'schema_version':1,'kind':'edit_plan','position_encoding':'utf-16','source':{'kind':'benchmark'},'documents':[{'uri':uri,'text':baseline,'version':1}],'workspace_edit':{'changes':{uri:[{'range':{'start':{'line':0,'character':0},'end':{'line':0,'character':0}},'newText':'a'} for _ in range(1000)]}},'actual':[{'uri':uri,'text':'a'*1000+baseline}]}
            target.write_text(json.dumps(plan,ensure_ascii=False),encoding='utf-8');args=['check-edits',str(target),'--format','json']
        else:
            rs=[{'kind':'meta','schema_version':1,'position_encoding':'utf-16','capture_mode':'fragment','provenance':'synthetic','producer':'deterministic-benchmark-v1'}]
            def message(seq,method,params):return {'kind':'message','seq':seq,'direction':'client_to_server','message':{'jsonrpc':'2.0','method':method,'params':params}}
            rs.append(message(1,'textDocument/didOpen',{'textDocument':{'uri':uri,'version':1,'text':baseline,'languageId':'text'}}))
            if mode=='multi-document':rs.append(message(2,'textDocument/didOpen',{'textDocument':{'uri':'file:///other','version':1,'text':baseline,'languageId':'text'}}))
            seq=len(rs)
            for i in range(count):
                change={'text':baseline} if mode=='full-replace' else {'range':{'start':{'line':0,'character':0},'end':{'line':0,'character':2 if baseline.startswith('🌙') else 1}},'text':'🌙' if baseline.startswith('🌙') else 'x'}
                rs.append(message(seq+i,'textDocument/didChange',{'textDocument':{'uri':uri,'version':i+2},'contentChanges':[change]}))
            rs.append({'kind':'checkpoint','seq':seq+count,'uri':uri,'version':count+1,'text':baseline,'source':'independent-generated-unchanged-text'})
            target.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs),encoding='utf-8');args=['audit',str(target),'--format','json']
        samples=[];error=None
        for iteration in range(6):
            start=time.perf_counter()
            p=subprocess.Popen([str(exe),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            try:stdout,stderr=p.communicate(timeout=120)
            except subprocess.TimeoutExpired:p.kill();p.communicate();error='timeout';break
            elapsed=time.perf_counter()-start
            try:r=json.loads(stdout);assert p.returncode==0 and r['analysis_complete'] is True
            except Exception:error={'exit':p.returncode,'stderr':stderr.decode('utf-8','replace')[:300]};break
            if iteration:samples.append({'seconds':elapsed,'memory':peak_memory(p)})
        results.append({'mode':mode,'requested_baseline_bytes':size,'actual_baseline_bytes':len(baseline.encode('utf-8')),'edits':1000 if mode=='batch-textedit' else count,'input_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'input_bytes':target.stat().st_size,'warmups':1,'samples':samples,'error':error,'median_seconds':statistics.median(x['seconds'] for x in samples) if len(samples)==5 else None,'spread_seconds':max(x['seconds'] for x in samples)-min(x['seconds'] for x in samples) if samples else None})
    home=ROOT/'.tooling/moon/bin'/('moon.exe' if os.name=='nt' else 'moon')
    evidence={'generator':'deterministic-v1; no random sampling','os':platform.platform(),'cpu':platform.processor(),'toolchain':subprocess.check_output([home,'version','--all']).decode('utf-8','replace'),'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'working_tree_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip()),'build':'native debug (existing validated artifact)','binary_sha256':hashlib.sha256(exe.read_bytes()).hexdigest(),'quick':a.quick,'results':results,'performance_superiority_claim':False}
    (out/'benchmark.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'report':str(out/'benchmark.json'),'scenarios':len(results),'failures':sum(x['error'] is not None for x in results)}))
    if any(x['error'] for x in results):raise SystemExit(1)

if __name__=='__main__':main()

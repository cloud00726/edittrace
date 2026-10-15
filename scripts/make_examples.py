"""Write deterministic, explicitly synthetic examples; no production logic."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URI = 'file:///demo.mbt'
META = dict(kind='meta', schema_version=1, position_encoding='utf-16',
            capture_mode='fragment', provenance='synthetic', producer='edittrace-examples')

def msg(seq, method, params, direction='client_to_server'):
    return dict(kind='message', seq=seq, direction=direction,
                message=dict(jsonrpc='2.0', method='textDocument/'+method, params=params))

def opened(seq=1, text='abc', version=1, uri=URI):
    return msg(seq, 'didOpen', dict(textDocument=dict(uri=uri, languageId='moonbit',version=version,text=text)))

def change(seq, changes, version=2, uri=URI):
    return msg(seq, 'didChange', dict(textDocument=dict(uri=uri,version=version),contentChanges=changes))

def edit(sl, sc, el, ec, text, **kw):
    return dict(range=dict(start=dict(line=sl,character=sc),end=dict(line=el,character=ec)),text=text,**kw)

def checkpoint(seq, text, version=2, uri=URI, **kw):
    return dict(kind='checkpoint',seq=seq,uri=uri,version=version,text=text,source='hand-calculated-expected',**kw)

CASES = {
 'valid-unicode': ([opened(text='A🌙B\r\n你好'),change(2,[edit(0,3,0,4,'C')]),checkpoint(3,'A🌙C\r\n你好')],0),
 'valid-sequential': ([opened(),change(2,[edit(0,0,0,0,'X'),edit(0,1,0,2,'A')]),checkpoint(3,'XAbc')],0),
 'checkpoint-mismatch': ([opened(text='🌙ab'),change(2,[edit(0,2,0,3,'X')]),checkpoint(3,'🌙aX',label='expected-result')],1),
 'version-regression-recovered': ([opened(),change(2,[dict(text='bad')],version=1),change(3,[dict(text='recovered')],version=3),checkpoint(4,'recovered',version=3)],1),
 'unknown-document': ([change(1,[dict(text='no baseline')])],2),
 'column-clamp': ([opened(),change(2,[edit(0,99,0,100,'!')]),checkpoint(3,'abc!')],0),
 'surrogate-boundary': ([opened(text='A🌙B'),change(2,[edit(0,2,0,2,'!')])],2),
 'multi-document': ([opened(),opened(2,'other',1,'file:///other.mbt'),change(3,[dict(text='bad')],version=1),
                     change(4,[dict(text='good')],version=5,uri='file:///other.mbt'),
                     checkpoint(5,'good',5,'file:///other.mbt'),msg(6,'didClose',dict(textDocument=dict(uri=URI))),
                     opened(7,'new generation',-4),checkpoint(8,'new generation',-4)],1),
}

def write_trace(path, records):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in [META,*records])+'\n',encoding='utf-8')

def main():
    for name,(records,_) in CASES.items():
        write_trace(ROOT/'examples'/f'{name}.jsonl',records)
    (ROOT/'examples'/'expected.json').write_text(json.dumps({n:e for n,(_,e) in CASES.items()},indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()

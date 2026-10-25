"""Exercise new CLI behavior; XML is parsed independently, not by product code."""
import copy
import json
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from native_artifact import find_native_executable

ROOT = Path(__file__).resolve().parents[1]


def validate(exe, root=ROOT):
    checks = []
    def check(name, condition):
        checks.append({'name': name, 'passed': bool(condition)})
        if not condition:
            raise AssertionError(name)
    def run(*args):
        return subprocess.run([str(exe), *map(str,args)], cwd=root, capture_output=True, timeout=30)
    p = run('doctor', '--format', 'json')
    r = json.loads(p.stdout)
    check('doctor capabilities', p.returncode == 0 and r['bridge_protocol'] == 1 and r['case_schema'] == 1 and r['core_version'] == '0.3.0')
    check('doctor text is actionable', b'Core executable:' in run('doctor').stdout)
    check('doctor rejects unsupported options', run('doctor', '--platform', 'fabricated').returncode == 2)
    original = json.loads((root/'examples/real-world/suite.json').read_text(encoding='utf-8'))
    good = original['cases'][0]
    bad = copy.deepcopy(good)
    bad['name'] = 'failed <assertion> & "unicode 🌙"\x01'
    bad['expect']['texts'][0]['text'] = 'PRIVATE_SOURCE_SENTINEL'
    broken = {'schema_version':1,'kind':'case','name':'malformed','input':{}}
    suite = {'schema_version':1,'kind':'suite','cases':[good,bad,broken,original['cases'][-1],good]}
    with tempfile.TemporaryDirectory(prefix='maintenance-',dir=root/'artifacts') as temp:
        source = Path(temp)/'suite.json'; source.write_text(json.dumps(suite,ensure_ascii=False),encoding='utf-8')
        p=run('suite','run',source,'--format','junit')
        tree=ET.fromstring(p.stdout)
        check('JUnit process preserves incomplete exit 2',p.returncode==2)
        check('JUnit counts failures and execution errors',tree.tag=='testsuite' and tree.attrib=={'name':'EditTrace','tests':'5','failures':'1','errors':'1'})
        entries=tree.findall('testcase')
        check('JUnit XML unicode escaping and invalid XML control replacement',entries[1].get('name')=='failed <assertion> & "unicode 🌙"\ufffd')
        check('JUnit error case does not stop later cases',len(entries)==5 and entries[-1].find('failure') is None and entries[-1].find('error') is None)
        check('JUnit preserves expected fault as passing',entries[3].find('failure') is None and entries[3].find('error') is None)
        check('JUnit default excludes raw source text',b'PRIVATE_SOURCE_SENTINEL' not in p.stdout)
        check('JUnit distinguishes failure/error elements',entries[1].find('failure') is not None and entries[2].find('error') is not None)
        output=Path(temp)/'result.xml'
        check('JUnit exclusive output succeeds',run('suite','run',source,'--format','junit','--out',output).returncode==2 and output.exists())
        before=output.read_bytes()
        check('JUnit output never overwrites',run('suite','run',source,'--format','junit','--out',output).returncode==2 and output.read_bytes()==before)
        for cases,expected in [([good],0),([bad,good],1)]:
            source.write_text(json.dumps({'schema_version':1,'kind':'suite','cases':cases}),encoding='utf-8')
            p=run('suite','run',source,'--format','junit')
            check('JUnit complete exit '+str(expected),p.returncode==expected and ET.fromstring(p.stdout).get('errors')=='0')
    p=run('check-edits','examples/real-world/rename.plan.json','--format','json')
    r=json.loads(p.stdout)
    check('core multi-file evidence summary',p.returncode==0 and len(r['documents'])>=2 and 'independent actual compared' in r['display_summary'])
    check('junit rejected outside suite',run('check-edits','examples/real-world/format.plan.json','--format','junit').returncode==2)
    evidence={'passed':len(checks),'checks':checks,'scope':'CLI via native core; JUnit parsed using Python ElementTree; not a user trial'}
    (root/'docs/maintenance-validation.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return evidence


if __name__ == '__main__':
    print(json.dumps(validate(find_native_executable(ROOT))))

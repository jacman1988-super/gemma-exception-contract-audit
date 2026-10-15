"""Post-outcome strengthening; never relabeled as the prospectively frozen v1 gate."""
import hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path

EXTRA='''
def test_existing_negative_error_message():
    with pytest.raises(ContractError) as caught:repair(-1,b"x")
    assert str(caught.value) == "bad"

def test_payload_identity_across_additional_domains():
    for payload in [b"bytes", {"item":7}, bytearray(b"abc"), [1,2]]:
        with pytest.raises(ContractError) as caught:repair(20,payload)
        assert caught.value.payload is payload
'''

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1];out=project/'results/exception-contract-resource'
    protocol=json.loads((out/'protocol.json').read_text());review=json.loads((out/'reviewed-model-patches.json').read_text())
    target=out/'posthoc-v2-evaluation.json'
    if target.exists():raise FileExistsError('Preserve prior outcomes')
    rules={'scope':__doc__,'extra_tests':EXTRA,'reason':'V1 lacked existing exception-message checks and used only one payload domain per task. Strengthen after inspecting model proposals and calibration; same outputs, no new inference.',
           'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'v1_protocol_sha256':hashlib.sha256((out/'protocol.json').read_bytes()).hexdigest()}
    (out/'posthoc-v2-protocol.json').write_text(json.dumps(rules,indent=2))
    rows=[]
    for case in protocol['cases']:
        reviewed=next(r for r in review['cases'] if r['id']==case['id']);edit=reviewed['edit']
        model=case['source'].replace(edit['old'],edit['new'])
        assert hashlib.sha256(model.encode()).hexdigest()==reviewed['patched_sha256']
        for variant,source in [('reference',case['reference']),('model',model),*case['mutants'].items()]:
            work=base/'work'/('eca-v2-'+case['id']+'-'+variant+'-'+str(time.time_ns()));work.mkdir(parents=True)
            (work/'subject.py').write_text(source);(work/'test_contract.py').write_text(case['contract_tests']+EXTRA)
            env=os.environ.copy();env['PYTHONPATH']=str(work)+os.pathsep+env.get('PYTHONPATH','');env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
            p=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','test_contract.py','--junitxml=results.xml'],cwd=work,env=env,capture_output=True,text=True,timeout=45)
            if p.returncode not in [0,1]:raise RuntimeError(p.stdout+p.stderr)
            tests=list(ET.parse(work/'results.xml').getroot().iter('testcase'));assert len(tests)==6
            rows.append({'id':case['id'],'variant':variant,'passed':p.returncode==0,'stdout':p.stdout,'stderr':p.stderr,'failed_tests':[t.attrib['name'] for t in tests if t.find('failure') is not None]})
        print(case['id'],'v2 audited',flush=True)
    summary={'scope':__doc__,'cases':rows,'model_passes':sum(r['variant']=='model' and r['passed'] for r in rows),'reference_passes':sum(r['variant']=='reference' and r['passed'] for r in rows),
             'mutants_rejected':sum(r['variant'] not in ['model','reference'] and not r['passed'] for r in rows),'model_rerun':False}
    target.write_text(json.dumps(summary,indent=2));print({k:v for k,v in summary.items() if k!='cases'})

if __name__=='__main__':run()

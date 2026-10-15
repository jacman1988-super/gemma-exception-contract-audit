"""Execute original calibration code, or only hash-matched reviewed model patches."""
import argparse,hashlib,json,os,subprocess,sys,time,xml.etree.ElementTree as ET
from pathlib import Path

def execute(project,case,variant,source):
    base=project.parents[1];out=project/'results/exception-contract-resource';work=base/'work'/('eca-'+case['id']+'-'+variant+'-'+str(time.time_ns()))
    work.mkdir(parents=True);(work/'subject.py').write_text(source)
    (work/'test_weak.py').write_text(case['weak_tests']);(work/'test_contract.py').write_text(case['contract_tests'])
    env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONPATH']=str(work)+os.pathsep+env.get('PYTHONPATH','')
    start=time.perf_counter()
    p=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','test_weak.py','test_contract.py','--junitxml=results.xml'],cwd=work,env=env,capture_output=True,text=True,timeout=45)
    if p.returncode not in [0,1]:raise RuntimeError(p.stdout+p.stderr)
    suites=ET.parse(work/'results.xml').getroot();groups={'weak':[],'contract':[]}
    for test in suites.iter('testcase'):
        name=test.attrib['classname'];group='weak' if 'test_weak' in name else 'contract'
        groups[group].append({'name':test.attrib['name'],'passed':test.find('failure') is None and test.find('error') is None and test.find('skipped') is None})
    if len(groups['weak'])!=3 or len(groups['contract'])!=4:raise ValueError('Unexpected collected tests')
    record={'id':case['id'],'variant':variant,'returncode':p.returncode,'groups':groups,'weak_pass':all(t['passed'] for t in groups['weak']),
            'contract_pass':all(t['passed'] for t in groups['contract']),'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'seconds':time.perf_counter()-start,'stdout':p.stdout,'stderr':p.stderr}
    return record

def run(mode):
    project=Path(__file__).resolve().parent;out=project/'results/exception-contract-resource';protocol=json.loads((out/'protocol.json').read_text());records=[]
    target=out/(mode+'-evaluation.json')
    if target.exists():raise FileExistsError('Preserve prior outcomes')
    if mode=='calibration':
        for case in protocol['cases']:
            for name,source in [('reference',case['reference']),('buggy',case['source']),*case['mutants'].items()]:
                records.append(execute(project,case,name,source))
            print(case['id'],'calibration complete',flush=True)
    else:
        reviewed=json.loads((out/'reviewed-model-patches.json').read_text())
        for row in reviewed['cases']:
            case=next(c for c in protocol['cases'] if c['id']==row['id'])
            if not row['accepted_for_execution']:
                records.append({'id':row['id'],'variant':'model','weak_pass':False,'contract_pass':False,'not_executed':True,'reason':row['reason']});continue
            if hashlib.sha256((out/(row['id']+'.output.txt')).read_bytes()).hexdigest()!=row['output_sha256']:raise ValueError('Model text changed')
            edit=row['edit'];source=case['source']
            if source.count(edit['old'])!=1:raise ValueError('Ambiguous edit')
            patched=source.replace(edit['old'],edit['new'])
            if hashlib.sha256(patched.encode()).hexdigest()!=row['patched_sha256']:raise ValueError('Reviewed patch differs')
            records.append(execute(project,case,'model',patched))
            print(row['id'],'weak',records[-1]['weak_pass'],'contract',records[-1]['contract_pass'],flush=True)
    summary={'cases':records,'complete':True,'mode':mode,'weak_pass_count':sum(r['weak_pass'] for r in records),'contract_pass_count':sum(r['contract_pass'] for r in records),
             'weak_only_count':sum(r['weak_pass'] and not r['contract_pass'] for r in records)}
    target.write_text(json.dumps(summary,indent=2));print({k:v for k,v in summary.items() if k!='cases'})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['calibration','model']);run(parser.parse_args().mode)

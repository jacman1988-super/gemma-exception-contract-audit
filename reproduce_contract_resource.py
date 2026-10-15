"""Recompute all three recorded resource stages in a fresh destination, without Gemma."""
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path

def semantic_outcomes(data):
    """Compare every case and assertion, excluding machine-specific logs/timing."""
    rows=[]
    for row in data['cases']:
        item={k:row[k] for k in ['id','variant','returncode','weak_pass','contract_pass','passed','failed_tests','source_sha256','not_executed'] if k in row}
        if 'groups' in row:item['groups']=row['groups']
        rows.append(item)
    return sorted(rows,key=lambda row:(row['id'],row['variant']))

def run(destination):
    project=Path(__file__).resolve().parent;source=project/'results/exception-contract-resource'
    destination.mkdir(parents=True,exist_ok=False);copy=destination/'outputs/gemma-importguard';copy.mkdir(parents=True)
    data=copy/'results/exception-contract-resource';data.mkdir(parents=True)
    for name in ['contract_resource_evaluate.py','contract_resource_audit_v2.py']:shutil.copy2(project/name,copy/name)
    for name in ['protocol.json','reviewed-model-patches.json',*[p.name for p in source.glob('*.output.txt')]]:shutil.copy2(source/name,data/name)
    for script,args in [('contract_resource_evaluate.py',['calibration']),('contract_resource_evaluate.py',['model']),('contract_resource_audit_v2.py',[])]:
        p=subprocess.run([sys.executable,str(copy/script),*args],env=os.environ.copy(),capture_output=True,text=True)
        (data/(script+('-'+args[0] if args else '')+'.log.txt')).write_text(p.stdout+p.stderr)
        if p.returncode:raise RuntimeError(p.stdout+p.stderr)
        print(script,args,'completed',flush=True)
    fields={'calibration-evaluation.json':['weak_pass_count','contract_pass_count','weak_only_count'],
            'model-evaluation.json':['weak_pass_count','contract_pass_count','weak_only_count'],
            'posthoc-v2-evaluation.json':['model_passes','reference_passes','mutants_rejected']}
    checks={}
    for name,keys in fields.items():
        expected=json.loads((source/name).read_text());actual=json.loads((data/name).read_text())
        if any(expected[k]!=actual[k] for k in keys):raise ValueError('Reproduction differs: '+name)
        if semantic_outcomes(expected)!=semantic_outcomes(actual):raise ValueError('Per-case reproduction differs: '+name)
        checks[name]={k:actual[k] for k in keys}
    (destination/'reproduction-check.json').write_text(json.dumps({'all_checks_passed':True,'every_case_and_assertion_compared':True,'model_rerun':False,'results':checks},indent=2))
    print('All resource outcome summaries reproduced exactly')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('destination',type=Path);run(parser.parse_args().destination.resolve())

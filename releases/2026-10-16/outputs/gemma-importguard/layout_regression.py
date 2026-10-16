"""Regression-only source-layout correction on already inspected upstream cases."""
import argparse,hashlib,json,shutil,time
from pathlib import Path
from importguard_layout import select
from expansion_benchmark import execute

def run(data,work,output):
    project=Path(__file__).resolve().parent
    frozen=json.loads((project/'results/expansion/protocol.json').read_text())
    assert frozen['selector_sha256']==hashlib.sha256((project/'importguard.py').read_bytes()).hexdigest()
    output.mkdir(parents=True,exist_ok=True)
    protocol={'kind':'post-outcome_regression_check','source_roots':['src'],
        'variant_sha256':hashlib.sha256((project/'importguard_layout.py').read_bytes()).hexdigest(),
        'unchanged_frozen_selector_sha256':frozen['selector_sha256'],
        'cases':[c['id'] for c in frozen['cases'] if c['package']=='cachetools'],
        'scope':'These cases revealed the source-layout issue. Reusing them checks the correction; it is not independent evidence or a scientific performance gain.'}
    if (output/'protocol.json').exists():raise FileExistsError('Preserve prior regression')
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    rows=[]
    for case in frozen['cases']:
        if case['id'] not in protocol['cases']:continue
        fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
        root=work/(case['id']+'-layout-'+str(time.time_ns()));shutil.copytree(fixed,root)
        for name in case['changed']:
            assert hashlib.sha256((buggy/name).read_bytes()).hexdigest()==case['parent_source_sha256'][name]
            shutil.copy2(buggy/name,root/name)
        choice=select(root,case['changed'],['src'])
        pool=set(case['pool']);static=sorted(set(choice['static_selected'])&pool);fallback=sorted(set(choice['selected'])&pool)
        assert static==fallback==sorted(case['pool'])
        outcome=execute(root,case,static)
        assert outcome['returncode']==1 and 'ERROR collecting' not in outcome['stdout']
        rows.append({'id':case['id'],'choice':choice,'static_pool':static,'fallback_pool':fallback,
            'test_result':outcome,'identical_selection_shares_one_test_run':True,
            'previous_static_modules':0,'corrected_static_modules':len(static)})
        print(case['id'],'static selection recovered',len(static),'modules; expected test failure detected',flush=True)
    (output/'results.json').write_text(json.dumps({'cases':rows,'generalization_claim':False,'module_saving_claim':False},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['data','work','output']:p.add_argument(n,type=Path)
    a=p.parse_args();run(*(getattr(a,n).resolve() for n in ['data','work','output']))

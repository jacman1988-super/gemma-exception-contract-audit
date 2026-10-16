"""Controlled discovery regression; no model inference or network."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from importguard_layout import select as old
from importguard_discovery import select as new

def main():
    project=Path(__file__).resolve().parent
    output=project/'results/discovery-regression';output.mkdir(parents=True,exist_ok=True)
    scratch=project.parents[1]/'work/discovery-regression';scratch.mkdir(parents=True,exist_ok=True)
    cases=[(layout,naming) for layout in ['flat','src'] for naming in ['prefix','suffix']]
    protocol={'cases':cases,'design':'Purpose-built post-review regression, not independent generalization or model evaluation',
              'source_sha256':{n:hashlib.sha256((project/n).read_bytes()).hexdigest() for n in ['importguard_layout.py','importguard_discovery.py','discovery_benchmark.py']},
              'mutation':'fee(n): 2*n -> 3*n','expected_test_pool':2}
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    results=[]
    for layout,naming in cases:
        root=scratch/(layout+'_'+naming);root.mkdir(exist_ok=True)
        source=root/('src/core.py' if layout=='src' else 'core.py');source.parent.mkdir(exist_ok=True)
        relevant='test_z_fee.py' if naming=='prefix' else 'fee_test.py'
        (root/relevant).write_text('from core import fee\ndef test_fee():\n    assert fee(3) == 6\n')
        (root/'test_a_unrelated.py').write_text('def test_unrelated():\n    assert 2 + 2 == 4\n')
        env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
        env['PYTHONPATH']=str(source.parent)+os.pathsep+env.get('PYTHONPATH','')
        def run(label,files):
            p=subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',*files],cwd=root,env=env,capture_output=True,text=True)
            (output/(layout+'_'+naming+'_'+label+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8')
            if p.returncode not in [0,1]:raise RuntimeError('Infrastructure failure: '+label)
            return p.returncode
        pool=['test_a_unrelated.py',relevant]
        source.write_text('def fee(n):\n    return 2*n\n');clean=run('clean',pool)
        if clean:raise RuntimeError('Clean fixture failed')
        source.write_text('def fee(n):\n    return 3*n\n');full=run('mutated_full',pool)
        if full!=1:raise RuntimeError('Mutation not exposed')
        record={'case':layout+'_'+naming,'clean_exit':clean,'mutated_full_exit':full,'full_modules':2}
        for name,selector in [('old',old),('new',new)]:
            choice=selector(root,[source.relative_to(root).as_posix()],source_roots=['src'] if layout=='src' else ['.'])
            record[name]={'selection':choice,'exit':run(name,choice['selected'])}
        results.append(record)
    summary={'cases':results,'old_detected':sum(r['old']['exit']==1 for r in results),'new_detected':sum(r['new']['exit']==1 for r in results),'case_count':len(results),'model_inference':False}
    (output/'results.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps({k:v for k,v in summary.items() if k!='cases'},indent=2))

if __name__=='__main__':main()

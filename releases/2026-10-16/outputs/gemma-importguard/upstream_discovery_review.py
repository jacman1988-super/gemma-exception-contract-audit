"""Post-outcome verification on five existing upstream cases, not new holdouts."""
import hashlib,json,os,shutil,time
from pathlib import Path
from importguard_discovery import select
from expansion_benchmark import execute

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1]
    output=project/'results/upstream-discovery-review'
    output.mkdir(parents=True,exist_ok=False)
    frozen=json.loads((project/'results/expansion/protocol.json').read_text())
    protocol={'scope':__doc__,'cases':[c['id'] for c in frozen['cases']],
              'encoding':'UTF-8 explicitly enabled for all subprocesses',
              'selector_sha256':hashlib.sha256((project/'importguard_discovery.py').read_bytes()).hexdigest(),
              'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'pool':'Previously declared modules; no additions or case replacements'}
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2))
    os.environ['PYTHONUTF8']='1';rows=[]
    for case in frozen['cases']:
        data=base/'work/expansion';fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
        root=base/'work'/('review-'+case['id']+'-'+str(time.time_ns()));shutil.copytree(fixed,root)
        for name,digest in case['tests_sha256'].items():
            if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Test drift')
        reference=execute(root,case,case['pool'])
        for name in case['changed']:
            if hashlib.sha256((buggy/name).read_bytes()).hexdigest()!=case['parent_source_sha256'][name]:raise ValueError('Source drift')
            shutil.copy2(buggy/name,root/name)
        choice=select(root,case['changed'],[case['source_root']])
        paths=sorted(set(choice['selected'])&set(case['pool']))
        selected=execute(root,case,paths)
        full=selected if paths==sorted(case['pool']) else execute(root,case,case['pool'])
        row={'id':case['id'],'reference':reference,'choice':choice,'selected_paths':paths,'selected_run':selected,'full_run':full,'identical_pool_shares_run':paths==sorted(case['pool'])}
        row['reproduced']=reference['returncode']==0 and full['returncode']==1 and 'ERROR collecting' not in full['stdout']
        rows.append(row)
        print(case['id'],'reference',reference['returncode'],'selected',selected['returncode'],'modules',len(paths),'/',len(case['pool']),flush=True)
    summary={'cases':rows,'new_holdout':False,'model_inference':False,'reproduced':sum(r['reproduced'] for r in rows),'detected_reproduced':sum(r['reproduced'] and r['selected_run']['returncode']==1 for r in rows)}
    (output/'results.json').write_text(json.dumps(summary,indent=2))

if __name__=='__main__':run()

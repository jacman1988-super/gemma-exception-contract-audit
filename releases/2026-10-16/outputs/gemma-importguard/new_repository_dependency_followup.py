"""Prospective selector test on two previously unused repositories; no model inference."""
import hashlib,json,shutil,time
from pathlib import Path
from importguard_discovery import select
from expansion_benchmark import execute

def run():
    root=Path(__file__).resolve().parent;base=root.parents[1];data=base/'work/new-upstream'
    cases=json.loads((data/'cases.json').read_text());out=root/'results/new-repositories-freezegun'
    out.mkdir(parents=True,exist_ok=False)
    protocol={**cases,'selector_sha256':hashlib.sha256((root/'importguard_discovery.py').read_bytes()).hexdigest(),
              'harness_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'dependency_followup':'Original missing-freezegun failures retained. Added freezegun 1.5.5; same cases and tests, no replacements.', 'design':'Cases frozen before original outcomes; upstream tests changed in the chosen commit; fixed tests paired with parent package sources. No outcome-based exclusions or replacements.',
              'reference_rule':'Fixed exit 0; parent exit 1 without collection errors. Skipped/unreproduced cases retained.',
              'comparison':'Full declared changed-test pool versus selector intersection with that pool; no whole-repository savings claim.',
              'model_inference':False}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2))
    rows=[]
    for case in cases['cases']:
        fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
        work=base/'work'/(case['id']+'-run-'+str(time.time_ns()));shutil.copytree(fixed,work)
        source_hashes={}
        for name in case['changed']:source_hashes[name]={v:hashlib.sha256((p/name).read_bytes()).hexdigest() for v,p in [('fixed',fixed),('parent',buggy)]}
        for name,digest in case['tests_sha256'].items():
            if hashlib.sha256((work/name).read_bytes()).hexdigest()!=digest:raise ValueError('Test drift')
        reference=execute(work,case,case['pool'])
        for name in case['changed']:shutil.copy2(buggy/name,work/name)
        choice=select(work,case['changed'],[case['source_root']]);paths=sorted(set(choice['selected'])&set(case['pool']))
        full=execute(work,case,case['pool'])
        selected=full if paths==sorted(case['pool']) else execute(work,case,paths)
        reproduced=reference['returncode']==0 and full['returncode']==1 and 'ERROR collecting' not in full['stdout']
        rows.append({'id':case['id'],'reference':reference,'parent_full':full,'selection':choice,'selected_paths':paths,'parent_selected':selected,'source_hashes':source_hashes,'reproduced':reproduced,'identical_pool_shares_run':paths==sorted(case['pool'])})
        (out/'results.json').write_text(json.dumps({'cases':rows,'complete':len(rows)==len(cases['cases']),'model_inference':False},indent=2))
        (out/(case['id']+'-LICENSE.txt')).write_text(case['license_text'])
        print(case['id'],'reference',reference['returncode'],'parent',full['returncode'],'selected',selected['returncode'],'modules',len(paths),'/',len(case['pool']),flush=True)

if __name__=='__main__':run()

"""Two pinned upstream bug/fix pairs; pilot only, no model execution.

Consumes reviewed official GitHub archives and metadata, never fetches or joins.
Fixed-version tests are held constant when production code is reverted to parent.
The declared test pools are bounded subsets, not entire upstream test suites.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import time
from importguard import select

CASES=[{'id':'boltons-indexedset','repo':'mahmoud/boltons',
        'fixed':'a180020c760b532e8889f161d97d05647adfee8c',
        'changed':['boltons/setutils.py'],
        'pool':['tests/test_setutils.py','tests/test_iterutils.py','tests/test_listutils.py'],
        'license':'BSD-3-Clause','expected_failed_test':'test_indexed_set_update_multiple_iterables'},
       {'id':'more-itertools-bucket','repo':'more-itertools/more-itertools',
        'fixed':'67fcf640477c78605580f5ee703a54c73c1e7a8a',
        'changed':['more_itertools/more.py'],
        'pool':['tests/test_more.py','tests/test_recipes.py'],
        'license':'MIT','expected_failed_test':'test_falsey_validator_is_honoured'}]

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def run(root,paths):
    if not paths:return {'returncode':0,'modules':0,'seconds':0,'stdout':'No tests selected.','stderr':''}
    env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    # The checked-out source must precede any locally installed copy.
    env['PYTHONPATH']=str(root)+os.pathsep+env.get('PYTHONPATH','')
    start=time.perf_counter()
    proc=subprocess.run([sys.executable,'-B','-m','pytest','-q','--tb=short',*paths],
                        cwd=root,env=env,capture_output=True,text=True,timeout=180)
    return {'returncode':proc.returncode,'modules':len(paths),'seconds':time.perf_counter()-start,
            'stdout':proc.stdout,'stderr':proc.stderr}

def benchmark(data,out,work):
    out.mkdir(parents=True,exist_ok=True);work.mkdir(parents=True,exist_ok=True)
    prepared=[];manifest=[]
    for case in CASES:
        meta=json.loads((data/(case['id']+'.json')).read_text(encoding='utf-8-sig'))
        assert meta['sha']==case['fixed']
        fixed=next((data/(case['id']+'-fixed')).iterdir())
        buggy=next((data/(case['id']+'-buggy')).iterdir())
        assert meta['parents'][0]['sha'] in buggy.name
        execution=work/(case['id']+'-'+str(time.time_ns()))
        shutil.copytree(fixed,execution)
        license_path=fixed/'LICENSE'
        assert license_path.exists()
        license_copy=out/(case['id']+'-LICENSE.txt');shutil.copy2(license_path,license_copy)
        item={**case,'parent':meta['parents'][0]['sha'],
              'commit_url':meta['html_url'],'license_sha256':digest(license_path),
              'archives_sha256':{v:digest(data/(case['id']+'-'+v+'.zip')) for v in ['fixed','buggy']},
              'fixed_sources_sha256':{p:digest(fixed/p) for p in case['changed']},
              'parent_sources_sha256':{p:digest(buggy/p) for p in case['changed']},
              'test_files_sha256':{p:digest(fixed/p) for p in case['pool']}}
        prepared.append((case,fixed,buggy,execution));manifest.append(item)
    # Written before observing any executed upstream outcomes. This is a pilot
    # manifest, not evidence of prospective repository sampling or registration.
    (out/'pilot-manifest.json').write_text(json.dumps({'cases':manifest,
          'selector_sha256':digest(Path(__file__).with_name('importguard.py')),
          'harness_sha256':digest(__file__),
          'scope':'Two convenience-selected small fixes; not a held-out benchmark or real-agent experiment.'},indent=2))
    records=[]
    for case,fixed,buggy,root in prepared:
        print('Fixed reference:',case['id'],flush=True)
        clean=run(root,case['pool'])
        if clean['returncode']!=0:
            records.append({'id':case['id'],'status':'fixed_reference_failed','fixed':clean});continue
        for p in case['changed']:shutil.copy2(buggy/p,root/p)
        selection=select(root,case['changed'])
        pool=set(case['pool'])
        choices={'full_declared_pool':case['pool'],
                 'imports_fallback':[p for p in selection['selected'] if p in pool],
                 'imports_no_fallback':[p for p in selection['static_selected'] if p in pool]}
        cache={};runs={}
        for method,paths in choices.items():
            key=tuple(sorted(paths))
            if key not in cache:cache[key]=run(root,list(key))
            runs[method]=cache[key]
        full=runs['full_declared_pool']
        reproduced=full['returncode']==1 and case['expected_failed_test'] in full['stdout'] and 'ERROR collecting' not in full['stdout']
        seeds=[];budget=len(choices['imports_fallback'])
        for seed in range(20):
            paths=tuple(sorted(random.Random(seed).sample(case['pool'],budget)))
            if paths not in cache:cache[paths]=run(root,list(paths))
            seeds.append({'seed':seed,'selected':list(paths),'run':cache[paths]})
        records.append({'id':case['id'],'status':'reproduced' if reproduced else 'not_reproduced',
              'fixed':clean,'selection':selection,'choices':choices,'runs':runs,'random_equal_budget':seeds})
        print(case['id'],records[-1]['status'],{k:(v['returncode'],v['modules']) for k,v in runs.items()},flush=True)
    result={'python':sys.version,'platform':platform.platform(),'model_used':None,'cases':records,
            'scope':'Declared module subsets only. Upstream tests transferred to parent production code. Convenience pilot, no population claims; no coverage comparison or Gemma inference in this run.'}
    (out/'results.json').write_text(json.dumps(result,indent=2))
    print('Saved',out/'results.json')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data',type=Path);parser.add_argument('work',type=Path)
    parser.add_argument('--output',type=Path,default=Path('results/real-bugs-pilot'))
    a=parser.parse_args();benchmark(a.data.resolve(),a.output.resolve(),a.work.resolve())

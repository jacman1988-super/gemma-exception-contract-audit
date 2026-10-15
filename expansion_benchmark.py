"""Frozen-selector assessment on five prospectively chosen upstream changes.

No gold patch is supplied to inference. Source localization uses changed hunk
positions and is therefore oracle-assisted, not autonomous repository navigation.
"""
import argparse,ast,hashlib,json,os
from pathlib import Path
import re,shutil,subprocess,sys,time
from importguard import select

CASES=[
 {'id':'cachetools-empty','repo':'tkem/cachetools','package':'cachetools','source_root':'src',
  'pool':['tests/test_cache.py','tests/test_lru.py','tests/test_rr.py','tests/test_tlru.py']},
 {'id':'cachetools-growth','repo':'tkem/cachetools','package':'cachetools','source_root':'src',
  'pool':['tests/test_cache.py','tests/test_lru.py','tests/test_rr.py','tests/test_tlru.py']},
 {'id':'cachetools-stale','repo':'tkem/cachetools','package':'cachetools','source_root':'src',
  'pool':['tests/test_cache.py','tests/test_lru.py','tests/test_rr.py','tests/test_tlru.py']},
 {'id':'jmespath-float','repo':'jmespath/jmespath.py','package':'jmespath','source_root':'.',
  'pool':['tests/test_compliance.py','tests/test_parser.py','tests/test_search.py']},
 {'id':'jmespath-functions','repo':'jmespath/jmespath.py','package':'jmespath','source_root':'.',
  'pool':['tests/test_functions.py','tests/test_search.py']},
]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def execute(root,case,paths):
    if not paths:return {'returncode':0,'modules':0,'stdout':'No tests selected.','stderr':'','seconds':0}
    env=os.environ.copy();env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1';env['PYTHONDONTWRITEBYTECODE']='1'
    env.pop('JMESPATH_TEST',None)
    env['PYTHONPATH']=os.pathsep.join([str(root/case['source_root']),str(root),env.get('PYTHONPATH','')])
    start=time.perf_counter()
    try:
        proc=subprocess.run([sys.executable,'-B','-m','pytest','-q','--tb=short',*paths],cwd=root,
                env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
        return {'returncode':proc.returncode,'modules':len(paths),'stdout':proc.stdout,'stderr':proc.stderr,'seconds':time.perf_counter()-start}
    except subprocess.TimeoutExpired:
        return {'returncode':None,'modules':len(paths),'stdout':'','stderr':'180-second test timeout','seconds':time.perf_counter()-start}

def prepare(data,out):
    if (out/'protocol.json').exists():raise FileExistsError('Use a fresh output directory')
    out.mkdir(parents=True,exist_ok=True);cases=[]
    for case in CASES:
        meta=json.loads((data/(case['id']+'.json')).read_text(encoding='utf-8-sig'))
        fixed=next((data/(case['id']+'-fixed')).iterdir())
        buggy=next((data/(case['id']+'-buggy')).iterdir())
        changed=[f['filename'] for f in meta['files'] if f['filename'].startswith(case['package']+'/') or f['filename'].startswith('src/'+case['package']+'/')]
        assert changed and all(n.endswith('.py') for n in changed)
        license_path=next(p for p in [fixed/'LICENSE',fixed/'LICENSE.txt'] if p.exists())
        shutil.copy2(license_path,out/(case['id']+'-LICENSE.txt'))
        cases.append({**case,'fixed':meta['sha'],'parent':meta['parents'][0]['sha'],'changed':changed,
              'url':meta['html_url'],'description':meta['commit']['message'],
              'archives_sha256':{v:sha(data/(case['id']+'-'+v+'.zip')) for v in ['fixed','buggy']},
              'fixed_source_sha256':{n:sha(fixed/n) for n in changed},
              'parent_source_sha256':{n:sha(buggy/n) for n in changed},
              'tests_sha256':{n:sha(fixed/n) for n in case['pool']},'license_sha256':sha(license_path)})
    protocol={'cases':cases,'selector_sha256':sha(Path(__file__).with_name('importguard.py')),
       'harness_sha256':sha(__file__),'created_before_test_execution':True,
       'selection':'Convenience sample from two previously unused repositories; source and dependency review before freezing, no outcomes used. Not random or population representative.',
       'exclusions_before_execution':['documentation-only changes','no included test change: cachetools-falsey, jmespath-sample','concurrency/race changes','legacy nose-generator compliance suite for jmespath-functions (not in declared pool)'],
       'reference_rule':'Fixed declared pool must pass, reverted source must yield pytest exit 1 without collection errors. Retain all failed references in denominator and logs; no replacement cases.',
       'model_rule':'Only reproduced cases eligible. Same E2B revision, 2048 context, 192 generated tokens, temperature zero, seed 20261014, one attempt and no retry. No edits to frozen selector after outcomes.',
       'localization':'Buggy function snippets selected from old hunk positions, at most 6000 characters; commit message supplied, gold added/deleted patch text and regression tests withheld.',
       'scope':'Prospective evaluation relative to frozen selector, not independent task authorship or contamination-free model assessment.'}
    (out/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
    return protocol

def evaluate(data,work,out):
    protocol=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    assert protocol['selector_sha256']==sha(Path(__file__).with_name('importguard.py'))
    rows=[]
    for case in protocol['cases']:
        fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
        root=work/(case['id']+'-'+str(time.time_ns()));shutil.copytree(fixed,root)
        print('Reference:',case['id'],flush=True)
        reference=execute(root,case,case['pool'])
        record={'id':case['id'],'reference':reference,'status':'reference_failed'}
        if reference['returncode']==0:
            for name in case['changed']:shutil.copy2(buggy/name,root/name)
            choice=select(root,case['changed']);pool=set(case['pool'])
            choices={'full_declared_pool':case['pool'],
                     'imports_fallback':sorted(set(choice['selected'])&pool),
                     'imports_no_fallback':sorted(set(choice['static_selected'])&pool)}
            runs={};cache={}
            for name,paths in choices.items():
                key=tuple(sorted(paths))
                if key not in cache:cache[key]=execute(root,case,list(key))
                runs[name]=cache[key]
            full=runs['full_declared_pool']
            status='reproduced' if full['returncode']==1 and 'ERROR collecting' not in full['stdout'] else 'not_reproduced'
            record.update({'status':status,'selection':choice,'choices':choices,'runs':runs})
        rows.append(record)
        (out/'results.json').write_text(json.dumps({'cases':rows,'model_used':None,'complete':len(rows)==len(protocol['cases'])},indent=2))
        print(case['id'],record['status'],flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['freeze','evaluate'])
    for n in ['data','work','output']:p.add_argument(n,type=Path)
    a=p.parse_args()
    if a.mode=='freeze':prepare(a.data.resolve(),a.output.resolve())
    else:evaluate(a.data.resolve(),a.work.resolve(),a.output.resolve())

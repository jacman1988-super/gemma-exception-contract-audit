"""Original controlled fixtures: executed selection comparisons, no model claims.

Coverage is collected on the clean version, before mutation. Only generated code
is executed. The matrix is fixed in this source, not selected by observed scores.
"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import random
import subprocess
import sys
import tempfile
import time
from importguard import select
SELECTOR_FILE='importguard.py'

MODES=('direct','transitive','relative','dynamic','aliased_dynamic',
       'aliased_builtin','resource','package_init')

def fixture(mode):
    source={'core.py':'def fee(n):\n return n * 2\n',
            'unrelated.py':'def label():\n return "ok"\n'}
    wrapper='from core import fee\n'
    changed='core.py'
    if mode=='transitive':
        source['bridge.py']='from core import fee\n';wrapper='from bridge import fee\n'
    elif mode=='relative':
        source['pkg/__init__.py']=''
        source['pkg/core.py']=source.pop('core.py')
        source['pkg/bridge.py']='from .core import fee\n'
        wrapper='from pkg.bridge import fee\n';changed='pkg/core.py'
    elif mode=='dynamic':
        wrapper='import importlib\nfee=importlib.import_module("core").fee\n'
    elif mode=='aliased_dynamic':
        wrapper='from importlib import import_module as load\nfee=load("core").fee\n'
    elif mode=='aliased_builtin':
        wrapper='load=__import__\nfee=load("core").fee\n'
    elif mode=='resource':
        source['factor.txt']='2'
        source['core.py']='from pathlib import Path\ndef fee(n):\n return n*int(Path(__file__).with_name("factor.txt").read_text())\n'
        changed='factor.txt'
    elif mode=='package_init':
        source['pkg/__init__.py']=source.pop('core.py')
        wrapper='from pkg import fee\n';changed='pkg/__init__.py'
    for i in range(5):
        # A real but behaviorally irrelevant dependency makes alias blind spots
        # observable without the selector's empty-selection fallback hiding them.
        dependency='import core\n' if i==0 and mode in {'aliased_dynamic','aliased_builtin'} else ''
        source[f'test_{i}_unrelated.py']='import unittest\nimport unrelated\n'+dependency+'class Test(unittest.TestCase):\n def test_label(self): self.assertEqual(unrelated.label(),"ok")\n'
    source['test_9_fee.py']='import unittest\n'+wrapper+'class Test(unittest.TestCase):\n def test_fee(self): self.assertEqual(fee(3),6)\n'
    mutated='3' if mode=='resource' else 'def fee(n):\n return n*3\n'
    return source,changed,mutated

def run(root,paths,coverage=False):
    if not paths:return {'returncode':0,'tests_selected':0,'seconds':0,'stdout':'','stderr':'No tests selected; not executed.','executed_files':[]}
    # trace records Python execution; it cannot observe arbitrary resource reads.
    runner='''import json,pathlib,sys,trace,unittest
root=pathlib.Path.cwd().resolve()
suite=unittest.defaultTestLoader.loadTestsFromNames(sys.argv[1:])
tracer=trace.Trace(count=True,trace=False,ignoredirs=[sys.prefix])
result=tracer.runfunc(unittest.TextTestRunner(verbosity=1).run,suite)
files=sorted({str(pathlib.Path(f).resolve().relative_to(root)).replace(chr(92),'/') for f,line in tracer.results().counts if pathlib.Path(f).resolve().is_relative_to(root)})
print('COVERAGE_JSON:'+json.dumps(files))
sys.exit(0 if result.wasSuccessful() else 1)
'''
    args=[sys.executable,'-B']
    args+=['-c',runner] if coverage else ['-m','unittest']
    args += [p[:-3].replace('/','.') for p in paths]
    start=time.perf_counter()
    p=subprocess.run(args,cwd=root,capture_output=True,text=True,timeout=20)
    executed=[]
    for line in p.stdout.splitlines():
        if line.startswith('COVERAGE_JSON:'):executed=json.loads(line.split(':',1)[1])
    return {'returncode':p.returncode,'tests_selected':len(paths),'seconds':time.perf_counter()-start,
            'stdout':p.stdout,'stderr':p.stderr,'executed_files':executed}

def benchmark():
    records=[]
    for mode in MODES:
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source,changed,mutated=fixture(mode)
            for name,body in source.items():
                p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(body)
            tests=sorted(n for n in source if n.startswith('test_'))
            clean=run(root,tests);assert clean['returncode']==0,clean
            coverage={p:run(root,[p],True) for p in tests}
            assert all(r['returncode']==0 for r in coverage.values())
            covered=[p for p,r in coverage.items() if changed in r['executed_files']]
            (root/changed).write_text(mutated)
            selection=select(root,[changed])
            choices={'full':tests,'imports_fallback':selection['selected'],
                     'imports_no_fallback':selection['static_selected'],'clean_line_coverage':covered}
            runs={name:run(root,paths) for name,paths in choices.items()}
            assert runs['full']['returncode']==1,runs['full']
            for result in runs.values():
                if result['returncode']:
                    assert 'FAIL: test_fee' in result['stderr'] and 'ERROR:' not in result['stderr'],result
            # Execute each distinct subset once and retain the seed->subset mapping.
            cache={};random_rows=[];k=len(selection['selected'])
            for seed in range(20):
                subset=tuple(sorted(random.Random(seed).sample(tests,k)))
                if subset not in cache:cache[subset]=run(root,list(subset))
                random_rows.append({'seed':seed,'selected':list(subset),'run':cache[subset]})
            records.append({'fixture':mode,'changed':changed,
                'clean_sources_sha256':{n:hashlib.sha256(s.encode()).hexdigest() for n,s in source.items()},
                'mutated_sha256':hashlib.sha256(mutated.encode()).hexdigest(),
                'clean':clean,'clean_coverage':coverage,'selection':selection,'runs':runs,'random_equal_budget':random_rows})
            print(mode,{m:(r['returncode'],r['tests_selected']) for m,r in runs.items()},flush=True)
    methods=['full','imports_fallback','imports_no_fallback','clean_line_coverage']
    summary={m:{'faults_detected':sum(r['runs'][m]['returncode']==1 for r in records),
                'test_modules_run':sum(r['runs'][m]['tests_selected'] for r in records)} for m in methods}
    summary['random_equal_budget']={'mean_faults_detected':sum(sum(x['run']['returncode']==1 for x in r['random_equal_budget'])/20 for r in records),
                                  'test_modules_per_replicate':summary['imports_fallback']['test_modules_run'],'seeds':20}
    return {'kind':'controlled_adversarial_fixture_experiment','model_used':None,
        'python':sys.version,'platform':platform.platform(),'summary':summary,'cases':records,
        'benchmark_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'selector_file':SELECTOR_FILE,
        'selector_sha256':hashlib.sha256(Path(SELECTOR_FILE).read_bytes()).hexdigest(),
        'limitations':'Eight purpose-built cases, not real bug pairs or independent samples. Random arms match fallback test-count budget, not runtime. Coverage requires clean execution overhead. No Gemma model executed. No statistical generalization claimed.'}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=Path('results/stress-benchmark.json'))
    parser.add_argument('--selector',choices=['current','v1'],default='current')
    args=parser.parse_args()
    if args.selector=='v1':
        from importguard_v1_snapshot import select
        SELECTOR_FILE='importguard_v1_snapshot.py'
    result=benchmark();args.output.write_text(json.dumps(result,indent=2));print(json.dumps(result['summary'],indent=2))

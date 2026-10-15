"""Test only the exact two retry edits reviewed in this experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import time
from real_bug_benchmark import CASES,run

REVIEWED_NEW='''    def update(self, *others):
        "update(*others) -> add values from one or more iterables"
        if not others:
            return
        elif len(others) == 1:
            other = others[0]
        else:
            other = list(chain(*others))
        for o in other:
            self.add(o)'''

def evaluate(data,work,previous,out):
    case=CASES[0]
    first=json.loads((previous/'reviewed-patch-evaluation.json').read_text())['cases'][0]['suggestion']
    fixed=next((data/'boltons-indexedset-fixed').iterdir())
    buggy=next((data/'boltons-indexedset-buggy').iterdir())
    source=(buggy/'boltons/setutils.py').read_text(encoding='utf-8')
    assert source.count(first['old'])==1
    current=source.replace(first['old'],first['new'])
    protocol=json.loads((out/'protocol.json').read_text(encoding='utf-8'))
    assert hashlib.sha256(current.encode()).hexdigest()==protocol['current_file_sha256']
    cache={};records=[]
    for arm in protocol['arms']:
        output=out/(arm+'.output.txt');text=output.read_text(encoding='utf-8')
        block=re.search(r'```json\s*(.*?)\s*```',text,re.S)
        assert block,'No complete JSON block; stop rather than repairing model output'
        edit=json.loads(block.group(1))
        assert set(edit)=={'old','new'} and edit['new']==REVIEWED_NEW
        assert current.count(edit['old'])==1
        assert edit['old'].startswith('    def update(self, *others):')
        patched=current.replace(edit['old'],edit['new'])
        digest=hashlib.sha256(patched.encode()).hexdigest()
        reused=digest in cache
        if not reused:
            target=work/(arm+'-reviewed-'+str(time.time_ns()))
            shutil.copytree(fixed,target)
            (target/'boltons/setutils.py').write_text(patched,encoding='utf-8')
            cache[digest]=run(target,case['pool'])
        records.append({'arm':arm,'reviewed_by':'Codex; not participant approval',
             'review':'Exact displayed local function; list(chain(*others)) flattens iterables. No new external effects.',
             'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
             'edit':edit,'patched_source_text_sha256':digest,
             'reused_identical_patch_test_result':reused,'test_result':cache[digest]})
        print(arm,'test exit',cache[digest]['returncode'],'reused',reused,flush=True)
    (out/'reviewed-patch-evaluation.json').write_text(json.dumps({'cases':records,
        'unique_patch_test_runs':len(cache),'scope':'Same known development case. Identical patches share one test run; not independent performance repetitions.'},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['data','work','previous','output']:p.add_argument(name,type=Path)
    a=p.parse_args();evaluate(*(getattr(a,n).resolve() for n in ['data','work','previous','output']))

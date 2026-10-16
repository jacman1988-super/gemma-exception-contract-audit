"""Execute only the two small edits explicitly reviewed in this session."""
import hashlib,json,os
from pathlib import Path
import re,shutil,sys,time
P=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('data',type=Path);parser.add_argument('work',type=Path)
args=parser.parse_args()
from real_bug_benchmark import CASES,run
out=P/'results/local-model-direct-pilot'
approved={
 'boltons-indexedset':{'old':'        else:\n            other = chain(others)',
                      'new':'        else:\n            other = list(chain(others))'},
 'more-itertools-bucket':{'old':'        self._validator = validator or (lambda x: True)',
                         'new':'        self._validator = validator if validator is not None else (lambda x: True)'}}
records=[]
for case in CASES:
    output=out/(case['id']+'.output.txt');text=output.read_text(encoding='utf-8')
    block=re.search(r'```json\s*(.*?)\s*```',text,re.S)
    assert block
    suggestion=json.loads(block.group(1));assert suggestion==approved[case['id']]
    data=args.data.resolve()
    fixed=next((data/(case['id']+'-fixed')).iterdir());buggy=next((data/(case['id']+'-buggy')).iterdir())
    execution=args.work.resolve()/(case['id']+'-reviewed-model-'+str(time.time_ns()))
    shutil.copytree(fixed,execution)
    for name in case['changed']:shutil.copy2(buggy/name,execution/name)
    target=execution/case['changed'][0];source=target.read_text(encoding='utf-8')
    assert source.count(suggestion['old'])==1
    target.write_text(source.replace(suggestion['old'],suggestion['new']),encoding='utf-8')
    result=run(execution,case['pool'])
    records.append({'id':case['id'],'reviewed_by':'Codex; not human approval',
        'review':'Only the shown local assignment edit; no added imports, calls with external effects, or commands.',
        'suggestion':suggestion,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'single_line_format_followed':'\n' not in suggestion['old'] and '\n' not in suggestion['new'],
        'patched_file_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'test_result':result})
    print(case['id'],'pytest exit',result['returncode'],flush=True)
(out/'reviewed-patch-evaluation.json').write_text(json.dumps({'cases':records,
   'scope':'Reviewed snippets applied without repair to parent production code with fixed upstream tests. Same two convenience cases; no iterative agent or blind evaluation.'},indent=2))

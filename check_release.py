"""Read-only provenance and draft checks; no scientific readiness claim."""
import hashlib,json
from pathlib import Path

def check(project):
    read=lambda p:json.loads((project/p).read_text(encoding='utf-8'))
    sha=lambda p:hashlib.sha256((project/p).read_bytes()).hexdigest()
    author=read('author.json');paper=(project/'paper-draft.txt').read_text(encoding='utf-8')
    assert 'Author: '+author['full_name'] in paper and len(paper.split())<3000
    frozen=read('results/expansion/protocol.json')
    assert frozen['selector_sha256']==sha('importguard.py')
    assert frozen['harness_sha256']==sha('expansion_benchmark.py')
    layout=read('results/layout-regression/protocol.json')
    assert layout['variant_sha256']==sha('importguard_layout.py')
    assert len(read('results/layout-regression/results.json')['cases'])==3
    primary=read('results/expansion-model/reviewed-patch-evaluation.json')
    assert all(c['status']=='failed_declared_pool' for c in primary['cases'])
    return {'author':author['full_name'],'local_checks_passed':True,'draft_words':len(paper.split()),
        'frozen_selector_preserved':True,'negative_results_preserved':True,
        'published':False,'submitted':False,'contest_ready':False,
        'remaining_research':['Independent assessment for layout variant','Stronger baselines and agent study','Establish a defensible original contribution','Participant review']}

if __name__=='__main__':print(json.dumps(check(Path(__file__).resolve().parent),indent=2))

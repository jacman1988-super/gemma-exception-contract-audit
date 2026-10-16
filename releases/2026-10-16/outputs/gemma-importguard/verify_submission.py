"""Read-only audit of prepared paper-track content. No platform actions."""
import hashlib,json
from pathlib import Path

def verify(project):
    status=json.loads((project/'submission-package.json').read_text())
    for name,digest in status['files'].items():
        if hashlib.sha256((project/name).read_bytes()).hexdigest()!=digest:raise ValueError('Checksum differs: '+name)
    text=(project/'submission-writeup.txt').read_text(encoding='utf-8');words=len(text.split())
    if words>3000:raise ValueError('Writeup exceeds word limit')
    for section in ['Subtitle:','Author: Jacek Adamek','ABSTRACT','1. INTRODUCTION','2. RELATED WORK','3. METHODS','4. RESULTS','5. INTERPRETATION','REFERENCES']:
        if section not in text:raise ValueError('Missing section: '+section)
    resource=project/'results/exception-contract-resource';read=lambda name:json.loads((resource/name).read_text())
    protocol=read('protocol.json');model=read('model-evaluation.json');calibration=read('calibration-evaluation.json');v2=read('posthoc-v2-evaluation.json')
    if len(protocol['cases'])!=6 or sum(len(c['mutants']) for c in protocol['cases'])!=36:raise ValueError('Resource cardinality differs')
    if hashlib.sha256((project/'contract_resource.py').read_bytes()).hexdigest()!=protocol['generator_sha256']:raise ValueError('Generator differs')
    if model['weak_pass_count']!=6 or model['contract_pass_count']!=6:raise ValueError('V1 model outcome differs')
    if calibration['weak_only_count']!=35 or v2['model_passes']!=5 or v2['mutants_rejected']!=36:raise ValueError('Audit outcomes differ')
    ids={c['id'] for c in protocol['cases']}
    if {c['id'] for c in model['cases']}!=ids or len(model['cases'])!=6:raise ValueError('Model case identities differ')
    if not all(r['weak_pass'] and r['contract_pass'] for r in model['cases']):raise ValueError('Per-case v1 outcomes differ')
    by_key={(r['id'],r['variant']):r for r in calibration['cases']}
    if len(by_key)!=48 or len(calibration['cases'])!=48:raise ValueError('Calibration case identities differ')
    for case in protocol['cases']:
        reference=by_key[(case['id'],'reference')];buggy=by_key[(case['id'],'buggy')]
        if not reference['weak_pass'] or not reference['contract_pass'] or buggy['weak_pass']:raise ValueError('Invalid reference/buggy control')
        for variant in case['mutants']:
            if not by_key[(case['id'],variant)]['weak_pass']:raise ValueError('Calibration weak outcome differs')
    failed=[r for r in v2['cases'] if r['variant']=='model' and not r['passed']]
    if len(failed)!=1 or failed[0]['id']!='type_tuple' or failed[0]['failed_tests']!=['test_existing_negative_error_message']:
        raise ValueError('Reported v2 counterexample differs')
    if not all(r['passed'] for r in v2['cases'] if r['variant']=='reference'):raise ValueError('V2 reference failed')
    for name in ['submission-review.ipynb','submission-review-executed.ipynb']:
        notebook=json.loads((project/name).read_text())
        cell_ids=[c.get('id') for c in notebook['cells']]
        if any(not isinstance(value,str) or not value for value in cell_ids) or len(set(cell_ids))!=len(cell_ids):raise ValueError('Notebook cell IDs missing or duplicate')
    generations=read('generations.json')
    if not generations['complete'] or len(generations['cases'])!=6 or any(r['returncode']!=0 or r['timed_out'] for r in generations['cases']):raise ValueError('Inference incomplete')
    reproduction=json.loads((project/'results/exception-contract-resource/reproduction-check.json').read_text())
    if not reproduction['all_checks_passed'] or not reproduction.get('every_case_and_assertion_compared') or reproduction['model_rerun']:raise ValueError('Reproduction audit differs')
    return {'author':'Jacek Adamek','content_prepared_for_submission':True,'writeup_words_including_references':words,'required_sections_present':True,
            'resource_tasks':6,'calibration_variants':36,'resource_reproduction_passed':True,'model_complete_repair_for_itsdangerous_claimed':False,
            'independent_v2_validation_claimed':False,'published':False,'submitted':False,'external_actions_authorized':False}

if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))

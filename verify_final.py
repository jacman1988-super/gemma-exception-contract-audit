"""Read-only final report/provenance checks. Does not claim competition readiness."""
import hashlib,json
from pathlib import Path
from check_release import check

def verify(root):
    original=check(root);release=json.loads((root/'final-release.json').read_text())
    for name,digest in release['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Release checksum mismatch: '+name)
    paper=(root/'paper-final-review.txt').read_text(encoding='utf-8')
    if len(paper.split())>=3000 or 'Author: Jacek Adamek' not in paper:raise ValueError('Paper limit or author mismatch')
    reference=json.loads((root/'results/itsdangerous-reference-repair/validation.json').read_text())
    if any(reference[key]['returncode'] for key in ['primary','full_suite','additional_contract_tests']):raise ValueError('Reference repair not validated')
    for folder in ['itsdangerous-model-contract-feedback','itsdangerous-model-localized-feedback']:
        assessment=json.loads((root/'results'/folder/'patch-evaluation.json').read_text())
        if assessment['cases'][2]['full_suite']['returncode']!=1:raise ValueError('Negative result not retained')
    return {'original_checks':original,'final_report_words':len(paper.split()),'reference_repair_validated':True,'model_repair_claimed':False,'ready_for_local_review':True,'contest_ready':False,'submitted':False}

if __name__=='__main__':print(json.dumps(verify(Path(__file__).resolve().parent),indent=2))

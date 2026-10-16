"""Manually reconstructed upstream-equivalent repair, explicitly not model output."""
import difflib,hashlib,json,shutil,time
from pathlib import Path
from expansion_benchmark import execute
from evaluate_itsdangerous_localized_feedback import CONTRACT_TESTS

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1];data=base/'work/new-upstream';out=project/'results/itsdangerous-reference-repair'
    out.mkdir(parents=True,exist_ok=False)
    case=json.loads((data/'cases.json').read_text())['cases'][0]
    fixed=next((data/'itsdangerous-new-fixed').iterdir());buggy=next((data/'itsdangerous-new-buggy').iterdir());name=case['changed'][0]
    source=(buggy/name).read_text();old='except ValueError as exc:';new='except (ValueError, OSError) as exc:'
    if source.count(old)!=1:raise ValueError('Ambiguous repair target')
    patched=source.replace(old,new)
    patch=''.join(difflib.unified_diff(source.splitlines(True),patched.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
    (out/'repair.patch').write_text(patch)
    (out/'protocol.json').write_text(json.dumps({'origin':'Manually reconstructed equivalent of the already inspected public upstream correction; not a model repair or novel contribution.',
        'url':case['url'],'source_sha256':hashlib.sha256((buggy/name).read_bytes()).hexdigest(),
        'patched_text_sha256':hashlib.sha256(patched.encode()).hexdigest(),'patch_sha256':hashlib.sha256(patch.encode()).hexdigest(),
        'review':'Extends only existing datetime conversion catch, preserving payload=value, date_signed and exception chaining; no changes to decoder or direct conversion.'},indent=2))
    target=base/'work'/('itsdangerous-reference-ready-'+str(time.time_ns()));shutil.copytree(fixed,target)
    (target/name).write_text(patched);primary=execute(target,case,case['pool']);full=execute(target,case,['tests'])
    (target/'test_contract_review.py').write_text(CONTRACT_TESTS);contract=execute(target,case,['test_contract_review.py'])
    if any(r['returncode'] for r in [primary,full,contract]):raise RuntimeError('Reference repair failed validation')
    (out/'validation.json').write_text(json.dumps({'primary':primary,'full_suite':full,'additional_contract_tests':contract,'model_generated':False,'submitted':False},indent=2))
    (out/'LICENSE.txt').write_text(case['license_text']);print('Reference repair: upstream and contract tests pass')

if __name__=='__main__':run()

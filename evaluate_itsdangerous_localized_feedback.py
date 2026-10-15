"""Evaluate the exact locally reviewed generated function; no arbitrary patches."""
import ast,hashlib,json,re,shutil,time
from pathlib import Path
from expansion_benchmark import execute

REVIEWED_NEW='        try:\n            ts_int = bytes_to_int(base64_decode(ts_bytes))\n        except OSError:\n            pass'

CONTRACT_TESTS='import pytest\nfrom itsdangerous.timed import TimestampSigner\nfrom itsdangerous.exc import BadTimeSignature\n\ndef test_malformed_exception_keeps_original_payload():\n    with pytest.raises(BadTimeSignature) as caught:\n        TimestampSigner("secret-key").unsign(b"value.TgPVoaGhoQ.AGBfQ6G6cr07byTRt0zAdPljHOY")\n    assert caught.value.payload == b"value"\n    assert caught.value.date_signed is None\n\ndef test_valid_roundtrip():\n    signer=TimestampSigner("secret-key")\n    assert signer.unsign(signer.sign(b"value")) == b"value"\n\ndef test_direct_conversion_keeps_original_exception_family():\n    with pytest.raises((OSError,ValueError,OverflowError)):\n        TimestampSigner("secret-key").timestamp_to_datetime(21959264258072993)\n'

def run():
    project=Path(__file__).resolve().parent;base=project.parents[1];out=project/'results/itsdangerous-model-localized-feedback'
    text=(out/'output.txt').read_text(encoding='utf-8');match=re.search(r'```json\s*(.*?)\s*```',text,re.S)
    if not match:raise ValueError('No complete JSON; no repairs permitted')
    edit=json.loads(match.group(1))
    if set(edit)!= {'old','new'} or edit['new']!=REVIEWED_NEW:raise ValueError('Not the exact reviewed function')
    data=base/'work/new-upstream';case=json.loads((data/'cases.json').read_text())['cases'][0]
    fixed=next((data/'itsdangerous-new-fixed').iterdir());buggy=next((data/'itsdangerous-new-buggy').iterdir());name=case['changed'][0]
    source=(buggy/name).read_text();protocol=json.loads((out/'protocol.json').read_text())
    if hashlib.sha256((buggy/name).read_bytes()).hexdigest()!=protocol['source_sha256'] or source.count(edit['old'])!=1:raise ValueError('Source mismatch')
    patched=source.replace(edit['old'],edit['new']);ast.parse(patched)
    assessment={'reviewed_by':'Codex, not participant publication approval','review':'Only decoder handler changed to catch OSError. Failing datetime conversion remains outside this handler; no new external effects. No file/network/process effects. Exact generated code tested without correction.',
                'patch':edit,'output_sha256':hashlib.sha256((out/'output.txt').read_bytes()).hexdigest(),'patched_text_sha256':hashlib.sha256(patched.encode()).hexdigest(),
                'additional_test_scope':'Three post-outcome diagnostic tests: original bytes payload, valid roundtrip, direct conversion exceptions; not frozen upstream tests.', 'pretest_rule':'Record primary declared timed-test module and full test directory for fixed, parent and generated versions. Retain all failures; no retry after test feedback.'}
    (out/'reviewed-patch.json').write_text(json.dumps(assessment,indent=2))
    rows=[]
    for variant in ['fixed','parent','generated']:
        target=base/'work'/('itsdangerous-'+variant+'-'+str(time.time_ns()));shutil.copytree(fixed,target)
        if variant=='parent':(target/name).write_text(source,encoding='utf-8')
        if variant=='generated':(target/name).write_text(patched,encoding='utf-8')
        primary=execute(target,case,case['pool']);full=execute(target,case,['tests'])
        (target/'test_contract_review.py').write_text(CONTRACT_TESTS)
        contract=execute(target,case,['test_contract_review.py'])
        rows.append({'variant':variant,'primary':primary,'full_suite':full,'additional_contract_tests':contract})
        print(variant,'primary',primary['returncode'],'full',full['returncode'],flush=True)
    (out/'patch-evaluation.json').write_text(json.dumps({'cases':rows,'patch_manually_corrected':False,'submitted':False},indent=2))

if __name__=='__main__':run()

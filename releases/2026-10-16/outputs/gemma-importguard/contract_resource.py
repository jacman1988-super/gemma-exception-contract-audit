"""Six original exception-contract diagnostics. Development resource, not population sample."""
import hashlib,json
from pathlib import Path

SPECS=[('os_bytes','OSError',"b'alpha'"),('overflow_mapping','OverflowError',"{'item': 7}"),
       ('key_text','KeyError',"'source'"),('index_buffer','IndexError',"bytearray(b'abc')"),
       ('type_tuple','TypeError',"('a', 3)"),('division_list','ZeroDivisionError',"[1, 2]")]

def case(identifier,secondary,payload):
    source=f'''class ContractError(Exception):
    def __init__(self, message, payload=None, stamp=None):
        super().__init__(message)
        self.payload = payload
        self.stamp = stamp

def low_level(value):
    if value == 999:
        raise RuntimeError("unrelated")
    if value < 0:
        raise ValueError("negative")
    if value > 10:
        raise {secondary}("range")
    return value * 2

def repair(value, payload):
    try:
        return low_level(value)
    except ValueError as exc:
        raise ContractError("bad", payload=payload, stamp=None) from exc
'''
    reference=source.replace('except ValueError as exc:',f'except (ValueError, {secondary}) as exc:')
    weak='''import pytest
from subject import repair,ContractError

def test_valid():
    assert repair(2,b"x") == 4

def test_negative():
    with pytest.raises(ContractError):repair(-1,b"x")

def test_new_range_error():
    with pytest.raises(ContractError):repair(20,b"x")
'''
    strong=f'''import pytest
from subject import repair,low_level,ContractError

def test_new_error_contract():
    payload={payload}
    with pytest.raises(ContractError) as caught:repair(20,payload)
    assert caught.value.payload is payload
    assert caught.value.stamp is None
    assert isinstance(caught.value.__cause__,{secondary})

def test_direct_helper_contract():
    with pytest.raises({secondary}):low_level(20)

def test_unrelated_error_propagates():
    with pytest.raises(RuntimeError):repair(999,b"x")

def test_other_valid_inputs():
    for value in [0,1,3,10]:assert repair(value,b"x") == 2*value
'''
    mutants={
        'payload_string':reference.replace('payload=payload','payload=str(payload)'),
        'lost_cause':reference.replace('from exc','from None'),
        'changed_stamp':reference.replace('stamp=None) from exc','stamp=0) from exc'),
        'overbroad_catch':reference.replace(f'except (ValueError, {secondary}) as exc:','except Exception as exc:'),
        'changed_helper':reference.replace(f'raise {secondary}("range")','raise ContractError("bad")'),
        'unseen_valid_regression':reference.replace('return low_level(value)','return low_level(value) if value == 2 else low_level(value) + 1')}
    prompt=('Fix the supplied Python function repair so out-of-range inputs are wrapped as ContractError. '
            'Preserve unrelated behavior, original payload object, stamp=None and exception chaining. '
            'Do not alter low_level or ContractError. Return only JSON with string fields old and new for one exact minimal source replacement. No commands.\nSource:\n'+source)
    return {'id':identifier,'secondary':secondary,'payload_expression':payload,'source':source,'reference':reference,'weak_tests':weak,'contract_tests':strong,'mutants':mutants,'prompt':prompt}

def freeze(destination):
    destination.mkdir(parents=True,exist_ok=False)
    cases=[case(*spec) for spec in SPECS]
    data={'resource':'Exception Contract Audit, version 1','author':'Jacek Adamek','license':'Apache-2.0',
          'design':'Six related constructed diagnostics inspired by the inspected ItsDangerous failure. Not independent task authorship or generalization; all cases, tests, mutants and prompts fixed before new model outcomes.',
          'evaluation':'Three visible-style weak tests versus four additional contract tests. References must pass both; buggy source must fail weak. Six deliberately flawed calibration mutants per case; retain all outcomes.',
          'model_rule':'One response per case, 512 tokens, 4096 context, temperature 0, seed 20261015, two CPU threads. No retries or evaluation feedback. Test/reference/mutant source withheld from prompt.',
          'cases':cases,'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (destination/'protocol.json').write_text(json.dumps(data,indent=2))
    return data

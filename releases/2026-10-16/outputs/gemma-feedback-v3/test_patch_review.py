import pytest
from evaluate_feedback import parse
from evaluate_round2 import apply_edits

def test_duplicate_json_keys_are_rejected():
    with pytest.raises(ValueError,match='Duplicate'):parse('```json\n{"edits":[],"edits":[]}\n```')

def test_truncated_response_is_rejected():
    with pytest.raises(ValueError):parse('```json\n{"edits":[{"file":"x.py","old":"a","new":"b')

def test_no_op_is_rejected():
    with pytest.raises(ValueError,match='No-op'):apply_edits({'x.py':'a=1'},[{'file':'x.py','old':'a=1','new':'a=1'}])

def test_source_scope_cannot_be_extended():
    with pytest.raises(ValueError,match='scope'):apply_edits({'x.py':'a=1'},[{'file':'../test.py','old':'a=1','new':'a=2'}])

def test_syntax_error_does_not_modify_inputs():
    source={'x.py':'a=1'}
    with pytest.raises(SyntaxError):apply_edits(source,[{'file':'x.py','old':'a=1','new':'a=('}])
    assert source=={'x.py':'a=1'}

def test_nonunique_source_is_rejected():
    with pytest.raises(ValueError,match='unique'):apply_edits({'x.py':'a=1\na=1'},[{'file':'x.py','old':'a=1','new':'a=2'}])

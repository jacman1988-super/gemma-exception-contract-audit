import pytest
from function_evaluation import functions

def wrapped(answer):return 'prompt ... (truncated)\n'+answer+'\n\n[ Prompt: stats ]'

def test_bare_methods_keep_literal_body():
    text=wrapped('FILE: a.py\n    def f(self):\n        return 3\n\nFILE: b.py\n    async def f(self):\n        return 4')
    # Wrong function names must be rejected, not silently substituted.
    with pytest.raises(ValueError,match='declared function'):functions(text,{'changed':['a.py','b.py'],'package':'tenacity'})

def test_single_file_function_context_is_audited_and_not_applied():
    text=wrapped('```python\nimport re\nCONST=5\ndef is_valid_pylock_path(path):\n    return True\n```')
    edits=functions(text,{'changed':['src/packaging/pylock.py'],'package':'packaging'})
    assert edits[0]['ignored_module_context']==['Import','Assign']
    assert edits[0]['literal_function']=='def is_valid_pylock_path(path):\n    return True'

def test_missing_header_is_ambiguous_with_two_files():
    with pytest.raises(ValueError,match='Ambiguous'):functions(wrapped('def _run_wait(self):\n    pass'),{'changed':['a.py','b.py'],'package':'tenacity'})

def test_extra_file_is_rejected():
    with pytest.raises(ValueError,match='scope'):functions(wrapped('FILE: ../x.py\ndef _run_wait(self):\n    pass'),{'changed':['a.py'],'package':'tenacity'})

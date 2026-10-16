"""New filename examples never included in feedback."""
from pathlib import Path
import pytest
from packaging.pylock import is_valid_pylock_path

@pytest.mark.parametrize('name,expected',[
    ('pylock.production.toml',True),('pylock.a-b.toml',True),
    ('pylock.dev_2.toml',True),('pylock.środowisko.toml',True),
    ('pylock.prod.toml\n\n',False),('pylock.toml\n',False),
    ('pylock.prod.toml.old',False),('pylock.prod.2.toml',False),
    ('notpylock.prod.toml',False)])
def test_unseen_filename(name,expected):
    assert is_valid_pylock_path(Path(name)) is expected

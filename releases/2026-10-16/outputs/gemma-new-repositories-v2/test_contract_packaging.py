"""Additional local boundary controls, withheld from generation."""
from pathlib import Path
import pytest
from packaging.pylock import is_valid_pylock_path

@pytest.mark.parametrize('name,valid',[
    ('pylock.toml',True),('pylock.prod.toml',True),('pylock.spam.toml\n',False),
    ('pylock.spam.toml\r\n',False),('pylock.prod.toml.backup',False),
    ('prefix-pylock.prod.toml',False),('pylock..toml',False)])
def test_complete_filename(name,valid):
    assert is_valid_pylock_path(Path(name)) is valid

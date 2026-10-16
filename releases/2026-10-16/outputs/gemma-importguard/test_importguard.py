import tempfile
import unittest
from pathlib import Path
from importguard import select


class SelectionTests(unittest.TestCase):
    def check(self, files, changed):
        with tempfile.TemporaryDirectory() as tmp:
            for name, text in files.items():
                p = Path(tmp, name)
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text, encoding='utf-8')
            return select(tmp, changed)

    def test_transitive_and_unrelated(self):
        out = self.check({'core.py': '', 'wrapper.py': 'import core',
                          'test_yes.py': 'import wrapper', 'test_no.py': ''}, ['core.py'])
        self.assertEqual(out['selected'], ['test_yes.py'])
        self.assertFalse(out['fallback'])

    def test_dynamic_falls_back(self):
        out = self.check({'core.py': '', 'test_x.py': '__import__("core")', 'test_y.py': ''}, ['core.py'])
        self.assertTrue(out['fallback'])
        self.assertEqual(len(out['selected']), 2)

    def test_deletion_falls_back(self):
        self.assertTrue(self.check({'test_x.py': ''}, ['deleted.py'])['fallback'])

    def test_aliased_importlib_falls_back_with_nonempty_static_choice(self):
        out = self.check({'core.py': '', 'test_connected.py': 'import core',
                          'test_hidden.py': 'from importlib import import_module as load\nload("core")'}, ['core.py'])
        self.assertEqual(out['static_selected'], ['test_connected.py'])
        self.assertTrue(out['fallback'])
        self.assertEqual(len(out['selected']), 2)

    def test_transitive_builtin_alias_falls_back(self):
        out = self.check({'core.py': '', 'test_connected.py': 'import core',
                          'test_hidden.py': 'a=__import__\nb=a\nb("core")'}, ['core.py'])
        self.assertTrue(out['fallback'])
        self.assertEqual(len(out['selected']), 2)

    def test_syntax_error_falls_back(self):
        self.assertTrue(self.check({'bad.py': 'def (', 'test_x.py': ''}, ['bad.py'])['fallback'])

    def test_package_relative_import(self):
        out = self.check({'p/__init__.py': '', 'p/core.py': '', 'p/w.py': 'from . import core',
                          'test_x.py': 'from p.w import value', 'test_y.py': ''}, ['p/core.py'])
        self.assertEqual(out['selected'], ['test_x.py'])

    def test_unknown_configuration(self):
        self.assertTrue(self.check({'test_x.py': ''}, ['pyproject.toml'])['fallback'])

    def test_cycles_terminate(self):
        out = self.check({'a.py': 'import b', 'b.py': 'import a', 'test_x.py': 'import b'}, ['a.py'])
        self.assertEqual(out['selected'], ['test_x.py'])


if __name__ == '__main__':
    unittest.main()

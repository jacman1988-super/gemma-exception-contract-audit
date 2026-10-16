import tempfile,unittest
from pathlib import Path
from importguard_layout import select

class LayoutTests(unittest.TestCase):
    def check(self,files,changed,roots):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name,source in files.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source,encoding='utf-8')
            return select(root,changed,roots)

    def test_src_dependency_finds_relevant_test_only(self):
        out=self.check({'src/acme/__init__.py':'','src/acme/core.py':'',
                        'tests/test_yes.py':'from acme.core import value',
                        'tests/test_no.py':''},['src/acme/core.py'],['src'])
        self.assertEqual(out['selected'],['tests/test_yes.py']);self.assertFalse(out['fallback'])

    def test_relative_import_chain_under_source_root(self):
        out=self.check({'src/p/__init__.py':'','src/p/core.py':'','src/p/bridge.py':'from .core import value',
                        'tests/test_yes.py':'from p.bridge import value','tests/test_no.py':''},['src/p/core.py'],['src'])
        self.assertEqual(out['selected'],['tests/test_yes.py'])

    def test_package_initialization_still_requires_fallback(self):
        out=self.check({'src/p/__init__.py':'','tests/test_yes.py':'import p','tests/test_no.py':''},['src/p/__init__.py'],['src'])
        self.assertTrue(out['fallback']);self.assertEqual(out['static_selected'],['tests/test_yes.py'])
        self.assertEqual(len(out['selected']),2)

    def test_alias_uncertainty_is_preserved(self):
        out=self.check({'src/p/__init__.py':'','src/p/core.py':'',
                        'tests/test_yes.py':'from importlib import import_module as load\nload("p.core")',
                        'tests/test_no.py':''},['src/p/core.py'],['src'])
        self.assertTrue(out['fallback']);self.assertEqual(len(out['selected']),2)

    def test_duplicate_flat_and_src_names_trigger_fallback(self):
        out=self.check({'p/core.py':'','src/p/core.py':'','tests/test_yes.py':'import p.core','tests/test_no.py':''},['src/p/core.py'],['.','src'])
        self.assertTrue(out['fallback']);self.assertTrue(any('ambiguous module' in r for r in out['reasons']))

    def test_source_root_cannot_escape_repository(self):
        with self.assertRaises(ValueError):self.check({'test_x.py':''},['test_x.py'],['..'])

    def test_source_prefix_does_not_match_longer_directory_name(self):
        out=self.check({'src/p/core.py':'','src_extra/p/core.py':'',
                        'test_yes.py':'import src_extra.p.core','test_no.py':''},['src_extra/p/core.py'],['src'])
        self.assertEqual(out['selected'],['test_yes.py'])

import tempfile,unittest
from pathlib import Path
from importguard_discovery import select

class DiscoveryTests(unittest.TestCase):
    def check(self,target,patterns=None):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for name,text in {'core.py':'','test_unrelated.py':'',target:'from core import value'}.items():
                (root/name).write_text(text)
            return select(root,['core.py'],test_patterns=patterns or ('test*.py','*_test.py'))
    def test_suffix_test_is_not_lost_when_an_unrelated_prefix_test_exists(self):
        result=self.check('fee_test.py')
        self.assertEqual(result['selected'],['fee_test.py'])
        self.assertFalse(result['fallback'])
    def test_unittest_bare_prefix_supported(self):
        self.assertEqual(self.check('testfee.py')['selected'],['testfee.py'])
    def test_explicit_custom_pattern(self):
        self.assertEqual(self.check('spec_fee.py',['spec_*.py'])['selected'],['spec_fee.py'])

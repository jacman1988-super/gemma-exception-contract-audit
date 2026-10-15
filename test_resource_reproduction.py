import unittest
from reproduce_contract_resource import semantic_outcomes

class ResourceReproductionChecks(unittest.TestCase):
    def test_swapped_case_outcomes_cannot_hide_behind_equal_totals(self):
        a={'cases':[{'id':'a','variant':'model','passed':True},{'id':'b','variant':'model','passed':False}]}
        b={'cases':[{'id':'a','variant':'model','passed':False},{'id':'b','variant':'model','passed':True}]}
        self.assertNotEqual(semantic_outcomes(a),semantic_outcomes(b))
    def test_logs_timing_and_case_order_do_not_change_semantic_result(self):
        a={'cases':[{'id':'a','variant':'model','passed':True,'stdout':'path1','seconds':1},{'id':'b','variant':'reference','passed':False}]}
        b={'cases':[{'id':'b','variant':'reference','passed':False},{'id':'a','variant':'model','passed':True,'stdout':'path2','seconds':3}]}
        self.assertEqual(semantic_outcomes(a),semantic_outcomes(b))

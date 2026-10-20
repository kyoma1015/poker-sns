"""Hand-derived expectations, not self-generated snapshots or G11 baselines."""
import copy
import json
import unittest
from gto.native.settlement import FIXTURES, SettlementMismatch, reference_module, run_case

FIXTURE = json.loads(FIXTURES.read_text())


class SettlementFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = reference_module()
        cls.reference = cls.context.__enter__()
    @classmethod
    def tearDownClass(cls):
        cls.context.__exit__(None, None, None)
    def test_rejects_fixture_with_wrong_hand_derived_expected_result(self):
        case = copy.deepcopy(FIXTURE['cases'][0]); case['expected']['net'][0] += 1
        with self.assertRaises(SettlementMismatch): run_case(self.reference, FIXTURE['base_rules'], case)
    def test_rejects_illegal_fixture_actions(self):
        case = copy.deepcopy(FIXTURE['cases'][0]); case['actions'] = [999999]
        with self.assertRaisesRegex(ValueError, 'illegal action'): run_case(self.reference, FIXTURE['base_rules'], case)
    def test_rejects_invalid_rule_profile(self):
        case = copy.deepcopy(FIXTURE['cases'][0]); case['overrides']['rounding'] = 'implicit'
        with self.assertRaisesRegex(ValueError, 'rounding'): run_case(self.reference, FIXTURE['base_rules'], case)


def fixture_test(case):
    def check(self):
        result = run_case(self.reference, FIXTURE['base_rules'], case)
        self.assertEqual(result['status'], 'PASS')
        self.assertFalse(result['native_compared'])
    return check


for fixture in FIXTURE['cases']:
    setattr(SettlementFixtures, 'test_' + fixture['id'], fixture_test(fixture))

if __name__ == '__main__': unittest.main()

"""Future task: exact integer chip oracles, synthetic fixtures only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gto.native import settlement


class ChipOracleTypes(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(settlement.FIXTURES.read_text())

    def run_owned(self, fixture):
        with tempfile.TemporaryDirectory(prefix='pokerid-chip-oracle-test-') as directory:
            p = Path(directory) / 'owned.json'
            p.write_text(json.dumps(fixture))
            with patch.object(settlement, 'FIXTURES', p):
                return settlement.run_fixture_suite()

    def assert_rejected_before_reference(self, fixture):
        with patch.object(settlement, 'reference_module') as reference:
            with self.assertRaises(ValueError):
                self.run_owned(fixture)
            reference.assert_not_called()

    def test_boolean_zero_rake_cannot_masquerade_as_expected_integer(self):
        changed = 0
        for case in self.fixture['cases']:
            if case['expected'].get('rake') == 0:
                case['expected']['rake'] = False
                changed += 1
        self.assertGreater(changed, 0)
        with self.assertRaises(ValueError):
            self.run_owned(self.fixture)

    def test_equal_float_rake_is_not_an_integer_chip_oracle(self):
        for case in self.fixture['cases']:
            if 'rake' in case['expected']:
                case['expected']['rake'] = float(case['expected']['rake'])
        with self.assertRaises(ValueError):
            self.run_owned(self.fixture)

    def test_scalar_chip_fields_are_checked_before_reference(self):
        for field in ('rake',):
            for invalid in (False, 0.0, '0', None, []):
                with self.subTest(field=field, invalid=invalid):
                    fixture = copy.deepcopy(self.fixture)
                    fixture['cases'][-1]['expected'][field] = invalid
                    self.assert_rejected_before_reference(fixture)

    def test_vector_chip_fields_require_lists_of_exact_integers(self):
        for field in ('refund', 'net', 'pot_amounts', 'pot_rakes'):
            for invalid in ([False], [0.0], ['0'], [None], '0', {}, False, 0.0, 0, None):
                with self.subTest(field=field, invalid=invalid):
                    fixture = copy.deepcopy(self.fixture)
                    fixture['cases'][-1]['expected'][field] = invalid
                    self.assert_rejected_before_reference(fixture)

    def test_valid_integer_and_negative_net_expectations_are_preserved(self):
        self.assertTrue(any(value < 0 for case in self.fixture['cases']
                            for value in case['expected'].get('net', [])))
        result = self.run_owned(self.fixture)
        self.assertEqual((result['status'], result['case_count']), ('PASS', 17))

    def test_wrong_integer_rake_still_fails_actual_equality(self):
        self.fixture['cases'][0]['expected']['rake'] = 999999
        with self.assertRaises(settlement.SettlementMismatch):
            self.run_owned(self.fixture)

    def test_refund_vector_and_partial_expectations_remain_supported(self):
        expected = self.fixture['cases'][0]['expected']['refund']
        self.assertIsInstance(expected, list)
        self.assertTrue(expected)
        self.assertTrue(all(type(value) is int for value in expected))
        self.fixture['cases'][0]['expected'] = {'refund': expected}
        result = self.run_owned(self.fixture)
        self.assertEqual((result['status'], result['case_count']), ('PASS', 17))

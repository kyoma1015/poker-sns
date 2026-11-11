"""Pinned synthetic oracle gate. No native solver or historical data is used."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from gto.native import settlement


class SettlementExpectations(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads(settlement.FIXTURES.read_text())

    def run_owned(self, fixture):
        with tempfile.TemporaryDirectory(prefix='pokerid-expectations-test-') as directory:
            path = Path(directory) / 'owned.json'
            path.write_text(json.dumps(fixture))
            with patch.object(settlement, 'FIXTURES', path):
                return settlement.run_fixture_suite()

    def assert_preflight_rejects(self, fixture):
        with patch.object(settlement, 'reference_module') as reference:
            with self.assertRaises(ValueError):
                self.run_owned(fixture)
            reference.assert_not_called()

    def test_all_oracles_erased_cannot_report_pass(self):
        for case in self.fixture['cases']:
            case['expected'] = {}
        with self.assertRaises(ValueError):
            self.run_owned(self.fixture)

    def test_first_empty_oracle_is_rejected_before_reference(self):
        self.fixture['cases'][0]['expected'] = {}
        self.assert_preflight_rejects(self.fixture)

    def test_late_empty_oracle_is_rejected_before_any_case_runs(self):
        self.fixture['cases'][-1]['expected'] = {}
        self.assert_preflight_rejects(self.fixture)

    def test_missing_oracle_is_rejected_before_reference(self):
        del self.fixture['cases'][0]['expected']
        self.assert_preflight_rejects(self.fixture)

    def test_null_oracle_is_rejected_before_reference(self):
        self.fixture['cases'][0]['expected'] = None
        self.assert_preflight_rejects(self.fixture)

    def test_non_mapping_oracles_are_rejected_before_reference(self):
        for invalid in ([], '', 0, False, ['net']):
            with self.subTest(invalid=invalid):
                fixture = copy.deepcopy(self.fixture)
                fixture['cases'][0]['expected'] = invalid
                self.assert_preflight_rejects(fixture)

    def test_valid_seventeen_case_suite_is_preserved(self):
        result = self.run_owned(self.fixture)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['case_count'], 17)
        self.assertFalse(result['historical_baseline_used'])

    def test_wrong_nonempty_oracle_still_fails_comparison(self):
        self.fixture['cases'][0]['expected']['net'] = [999999]
        with self.assertRaises(settlement.SettlementMismatch):
            self.run_owned(self.fixture)

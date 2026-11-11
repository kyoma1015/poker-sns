"""Fixed synthetic validator regression; no native solver/checkpoint is needed."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from gto.native import settlement


class NonemptySettlement(unittest.TestCase):
    def run_with_cases(self, cases):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'owned-fixture.json'
            path.write_text(json.dumps({'schema': 'pokerid-synthetic-settlement-v1',
                                        'cases': cases, 'base_rules': {},
                                        'provenance': 'owned synthetic fixture'}))
            with patch.object(settlement, 'FIXTURES', path):
                return settlement.run_fixture_suite()

    def test_empty_suite_cannot_report_pass(self):
        with self.assertRaises(ValueError):
            self.run_with_cases([])

    def test_invalid_case_collection_rejected_before_loading_reference(self):
        for cases in ([], {}, '', None, False):
            with self.subTest(cases=cases):
                with patch.object(settlement, 'reference_module', side_effect=AssertionError('reference loaded before fixture gate')):
                    with self.assertRaises(ValueError):
                        self.run_with_cases(cases)

    def test_valid_real_synthetic_suite_keeps_nonzero_case_count(self):
        result = settlement.run_fixture_suite()
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['case_count'], 17)
        self.assertEqual(len(result['results']), 17)
        self.assertFalse(result['historical_baseline_used'])


if __name__ == '__main__': unittest.main()

"""Independent synthetic ranking fixtures, never strategy optimality claims."""
import unittest
from gto.native.settlement import run_rank7_fixture_suite, validate_rank7_cards


class Rank7Fixtures(unittest.TestCase):
    def test_all_categories_match_explicit_expectations(self):
        report = run_rank7_fixture_suite()
        self.assertEqual(report['case_count'], 16)
        self.assertFalse(report['historical_baseline_used'])
        self.assertFalse(report['strategy_or_convergence_proof'])
        results = {case['id']: case['rank'] for case in report['results']}
        self.assertEqual(results['board_tie_a'], results['board_tie_b'])
        self.assertGreater(results['pair_high_kicker'], results['pair_low_kicker'])

    def test_valid_card_input_is_copied(self):
        cards = list(range(7))
        result = validate_rank7_cards(cards)
        self.assertEqual(result, cards)
        self.assertIsNot(result, cards)

if __name__ == '__main__': unittest.main()

"""Exact toy-game BR oracle. No native artifacts or historical checkpoints."""
import importlib
import itertools
import math
import unittest


class ConvergenceMetrics(unittest.TestCase):
    def setUp(self):
        self.metrics = importlib.import_module('gto.convergence').matching_pennies_metrics

    def test_uniform_equilibrium_has_zero_gap(self):
        r = self.metrics([.5, .5], [.5, .5])
        self.assertEqual(r['nash_conv'], 0)
        self.assertEqual(r['exploitability'], 0)
        self.assertEqual(r['utility_p0'], 0)

    def test_pure_profile_has_two_player_gap_two(self):
        r = self.metrics([1, 0], [1, 0])
        self.assertEqual(r['utility_p0'], 1)
        self.assertEqual(r['utility_p1'], -1)
        self.assertEqual(r['nash_conv'], 2)
        self.assertEqual(r['exploitability'], 1)

    def test_independent_payoff_matrix_best_response_enumeration(self):
        matrix = ((1, -1), (-1, 1))
        for p, q in itertools.product((0, .25, .5, .75, 1), repeat=2):
            with self.subTest(p=p, q=q):
                x, y = [p, 1-p], [q, 1-q]
                u0 = sum(x[i]*y[j]*matrix[i][j] for i in range(2) for j in range(2))
                br0 = max(sum(y[j]*matrix[i][j] for j in range(2)) for i in range(2))
                br1 = max(sum(x[i]*-matrix[i][j] for i in range(2)) for j in range(2))
                expected = (br0-u0)+(br1+u0)
                r = self.metrics(x, y)
                self.assertAlmostEqual(r['utility_p0'], u0)
                self.assertAlmostEqual(r['utility_p1'], -u0)
                self.assertAlmostEqual(r['best_response_p0'], br0)
                self.assertAlmostEqual(r['best_response_p1'], br1)
                self.assertAlmostEqual(r['nash_conv'], expected)
                self.assertAlmostEqual(r['exploitability'], expected/2)

    def test_invalid_policy_shapes_are_rejected(self):
        for invalid in (None, {}, '', '01', [], [.5], [.5, .5, 0]):
            with self.subTest(invalid=invalid):
                for args in ((invalid, [.5, .5]), ([.5, .5], invalid)):
                    with self.assertRaises(ValueError): self.metrics(*args)

    def test_nonfinite_nonnumeric_boolean_and_out_of_range_rejected(self):
        for invalid in ([True, False], ['.5', '.5'], [None, 1], [math.nan, .5],
                        [math.inf, 0], [-math.inf, 1], [-.1, 1.1], [2, -1]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError): self.metrics(invalid, [.5, .5])

    def test_unnormalized_policies_are_not_silently_normalized(self):
        for invalid in ([0, 0], [.2, .2], [.8, .8], [.5, .5001]):
            with self.assertRaises(ValueError): self.metrics([.5, .5], invalid)

    def test_inputs_and_claim_boundaries_are_preserved(self):
        x, y = [.6, .4], [.3, .7]
        r = self.metrics(x, y)
        self.assertEqual(x, [.6, .4]); self.assertEqual(y, [.3, .7])
        self.assertAlmostEqual(r['nash_conv'], .6)
        self.assertEqual(r['game'], 'synthetic-matching-pennies-v1')
        self.assertIs(r['strategy_convergence_proof'], False)
        self.assertIs(r['historical_baseline_used'], False)

import unittest
from gto.abstract.flop_tree_ablation import Policy, evaluate_flop, compare_to_checkdown


class FlopTreeTests(unittest.TestCase):
    def test_everyone_checks(self):
        p = Policy(0, 0, 0, 0)
        for equity in (0, .2, .5, 1):
            self.assertAlmostEqual(evaluate_flop(equity, p, p), equity)

    def test_bet_and_fold(self):
        hero = Policy(1, 0, 0, 0)
        villain = Policy(0, 0, 0, 0)
        self.assertAlmostEqual(evaluate_flop(.1, hero, villain), 1)

    def test_hero_folds_to_bet(self):
        hero = Policy(0, 0, 0, 0)
        villain = Policy(1, 0, 0, 0)
        self.assertEqual(evaluate_flop(1, hero, villain), 0)

    def test_bet_call_showdown(self):
        hero = Policy(1, 0, 1, 1)
        villain = Policy(0, 0, 1, 1)
        self.assertAlmostEqual(evaluate_flop(.5, hero, villain), .5)
        self.assertAlmostEqual(evaluate_flop(1, hero, villain), 1.5)

    def test_raise_and_fold(self):
        hero = Policy(1, 0, 0, 0)
        villain = Policy(0, 1, 0, 0)
        self.assertAlmostEqual(evaluate_flop(.5, hero, villain), -.5)

    def test_raise_call(self):
        hero = Policy(1, 0, 0, 1)
        villain = Policy(0, 1, 0, 1)
        self.assertAlmostEqual(evaluate_flop(1, hero, villain), 2.5)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            Policy(1.1, 0, 0, 0)
        with self.assertRaises(ValueError):
            evaluate_flop(float("nan"), Policy(0, 0, 0, 0), Policy(0, 0, 0, 0))

    def test_unverified_is_explicit(self):
        result = compare_to_checkdown(.5, Policy(0, 0, 0, 0), Policy(0, 0, 0, 0))
        self.assertEqual(result["model_delta_pot_units"], 0)
        self.assertIsNone(result["external_gto_deviation"])
        self.assertFalse(result["validated_gto"])


if __name__ == "__main__":
    unittest.main()

import unittest
from gto.abstract.flop_tree_ablation import Policy
from gto.abstract.flop_reach_adapter import conditional_flop_ev


class ReachAdapterTests(unittest.TestCase):
    def setUp(self):
        n = 169
        self.p = [0.0] * (n*n)
        self.p[0] = 1.0
        self.e = [0.0] * (n*n)
        self.e[0] = .5
        self.r = [0.0] * n
        self.r[0] = 1.0
        self.check = Policy(0, 0, 0, 0)
        self.bet = Policy(1, 0, 0, 0)

    def run_ev(self, hero, villain, **overrides):
        args = dict(stage="vs_3bet", class_probability=self.p, hero_reach=self.r,
                    villain_reach=self.r, equity_by_pair=self.e,
                    hero_policy=hero, villain_policy=villain, pot_bb=9)
        args.update(overrides)
        return conditional_flop_ev(**args)

    def test_checkdown_delta_zero(self):
        x = self.run_ev(self.check, self.check)
        self.assertAlmostEqual(x["old_checkdown_ev_bb"], 4.5)
        self.assertAlmostEqual(x["model_delta_bb"], 0)

    def test_uncontested_bet_delta(self):
        x = self.run_ev(self.bet, self.check, stage="vs_4bet")
        self.assertAlmostEqual(x["new_flop_tree_ev_bb"], 9)
        self.assertAlmostEqual(x["model_delta_bb"], 4.5)
        self.assertIsNone(x["external_reference_deviation_bb"])
        self.assertFalse(x["full_game_gto_verified"])

    def test_zero_reach_rejected(self):
        with self.assertRaises(ValueError):
            self.run_ev(self.check, self.check, hero_reach=[0]*169)

    def test_shape_and_stage_validation(self):
        with self.assertRaises(ValueError):
            self.run_ev(self.check, self.check, equity_by_pair=[.5])
        with self.assertRaises(ValueError):
            self.run_ev(self.check, self.check, stage="rfi")


if __name__ == "__main__":
    unittest.main()

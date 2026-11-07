import unittest
from gto.abstract.model import tree
from gto.abstract.flop_tree_ablation import Policy
from gto.abstract.frozen_flop_ablation import evaluate_frozen_ablation


class FrozenFlopAblationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes = tree()
        cls.strategy = [0.0] * (len(nodes)*3*169)
        for i, node in enumerate(nodes):
            if node["actor"] >= 0:
                for a in range(len(node["actions"])):
                    for h in range(169):
                        cls.strategy[(i*3+a)*169+h] = 1/len(node["actions"])
        cls.kernel = {"models": ["allin_showdown"], "mean": [0.0]*(169*169)}

    def test_checkdown_both_stages(self):
        check = Policy(0, 0, 0, 0)
        for stage in ("vs_3bet", "vs_4bet"):
            result = evaluate_frozen_ablation(stage, self.strategy, self.kernel,
                                               check, check, pot_bb=9)
            self.assertAlmostEqual(result["old_checkdown_ev_bb"], 4.5)
            self.assertAlmostEqual(result["model_delta_bb"], 0)
            self.assertFalse(result["full_game_gto_verified"])

    def test_bet_fold_toy_difference(self):
        bet = Policy(1, 0, 0, 0)
        check = Policy(0, 0, 0, 0)
        result = evaluate_frozen_ablation("vs_3bet", self.strategy, self.kernel,
                                           bet, check, pot_bb=9)
        self.assertAlmostEqual(result["model_delta_bb"], 4.5)
        self.assertIsNone(result["external_gto_deviation_bb"])

    def test_reject_invalid_kernel(self):
        check = Policy(0, 0, 0, 0)
        with self.assertRaises(ValueError):
            evaluate_frozen_ablation("vs_4bet", self.strategy,
                                    {"mean": [101.0]*(169*169)},
                                    check, check, pot_bb=9)


if __name__ == "__main__":
    unittest.main()

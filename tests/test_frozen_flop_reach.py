import unittest
from gto.abstract.model import tree
from gto.abstract.frozen_flop_reach import frozen_reach


class FrozenReachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        nodes = tree()
        cls.uniform = [0.0] * (len(nodes)*3*169)
        for i, node in enumerate(nodes):
            if node["actor"] >= 0:
                for a in range(len(node["actions"])):
                    for h in range(169):
                        cls.uniform[(i*3+a)*169+h] = 1/len(node["actions"])

    def test_both_stages(self):
        for stage in ("vs_3bet", "vs_4bet"):
            result = frozen_reach(stage, self.uniform)
            self.assertGreater(result["conditional_mass"], 0)
            self.assertEqual(len(result["class_probability"]), 169*169)
            self.assertEqual(len(result["hero_reach"]), 169)
            self.assertIsNone(result["equity_by_pair"])
            self.assertFalse(result["full_game_gto_verified"])

    def test_reject_missing_strategy(self):
        with self.assertRaises(ValueError):
            frozen_reach("vs_3bet", [])

    def test_reject_invalid_probability(self):
        broken = list(self.uniform)
        broken[0] = float("nan")
        with self.assertRaises(ValueError):
            frozen_reach("vs_4bet", broken)

    def test_reject_unknown_stage(self):
        with self.assertRaises(ValueError):
            frozen_reach("rfi", self.uniform)


if __name__ == "__main__":
    unittest.main()

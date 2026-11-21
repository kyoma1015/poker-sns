"""Negative distribution-boundary stub; positive poker cases use NativeState."""
from pathlib import Path
import sys
import unittest
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.poker_oracle import exact_policy_value

class DistributionGuard(unittest.TestCase):
    def check(self,probability):
        class ChanceStub:
            def __init__(self,done=False):self.done=done
            def clone(self):return ChanceStub(self.done)
            def is_terminal(self):return self.done
            def is_chance_node(self):return True
            def chance_outcomes(self):return [(0,probability)]
            def apply_action(self,a):self.done=True
            def returns(self):return [1.,-1.]
        with self.assertRaisesRegex(ValueError,'uniform-card chance'):
            exact_policy_value(ChanceStub(),lambda node:{0:Fraction(1)},max_nodes=3)
    def test_nan_is_not_a_uniform_probability(self):self.check(float('nan'))
    def test_infinity_is_not_a_uniform_probability(self):self.check(float('inf'))
    def test_negative_is_not_a_uniform_probability(self):self.check(-1.)

if __name__=='__main__':unittest.main()

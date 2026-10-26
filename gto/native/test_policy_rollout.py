"""Compare sampled native values with independent exact native-tree evaluation."""
from fractions import Fraction
import importlib
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.preflop import decision
from gto.native.poker_oracle import exact_policy_value
from gto.native.policy_rollout import policy_value


class Rollout(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def state(self, **rules):
        return decision(self.native,NativeGame([20,20],**rules),[],cards=[48,49,0,1])

    def test_preflop_fold_exact_and_nonmutation(self):
        state=self.state(); before=state.audit()
        policy=lambda node:{0:Fraction(1)}
        exact=exact_policy_value(state,policy)
        sampled=policy_value(state,policy,samples=20,seed=17)
        self.assertEqual(sampled['values'],exact['values'])
        self.assertEqual(state.audit(),before)
        self.assertEqual(sum(sampled['values']),-sampled['mean_rake'])

    def test_turn_river_against_exact_oracle_with_rake_and_ante(self):
        for rules in ({},{'bba':2},{'rake_num':1,'rake_den':10,'rake_cap':10}):
            state=self.state(**rules)
            for a in [22,1,8,17,26,32]: state.apply_action(a)
            policy=lambda node:{1:Fraction(1)}
            exact=exact_policy_value(state,policy,max_nodes=100)
            sampled=policy_value(state,policy,samples=2000,seed=17)
            for p,value in enumerate(exact['values']):
                lo,hi=sampled['simultaneous_chip_intervals'][p]
                self.assertLessEqual(lo,float(value));self.assertGreaterEqual(hi,float(value))
                self.assertLess(abs(float(sampled['values'][p]-value)),1)
            self.assertEqual(sum(sampled['values']),-sampled['mean_rake'])

    def test_reproducibility(self):
        policy=lambda node:{1:Fraction(1)}
        a=policy_value(self.state(),policy,samples=20,seed=4)
        self.assertEqual(a,policy_value(self.state(),policy,samples=20,seed=4))

    def test_bad_policy_and_budget_fail_closed(self):
        state=self.state()
        for policy in (lambda n:{1:Fraction(1,2)},lambda n:{2:Fraction(1)},lambda n:{}):
            with self.assertRaises(ValueError):policy_value(state,policy,samples=2,seed=1)
        with self.assertRaises(ValueError):
            policy_value(state,lambda n:{1:Fraction(1)},samples=2,seed=1,max_steps=1)


if __name__=='__main__':unittest.main()

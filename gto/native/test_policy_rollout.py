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
from gto.native.policy_rollout import policy_value, belief_value, action_values


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

    def test_preflop_belief_exact_fold_value(self):
        game=NativeGame([20,20])
        result=belief_value(self.native,game,[48,49],
            [([0,1],Fraction(1,4)),([2,3],Fraction(3,4))],[],[],
            lambda node:{0:Fraction(1)},samples_per_deal=10,seed=17)
        self.assertEqual(result['sample_mean_values'],[Fraction(-1),Fraction(1)])
        self.assertEqual(result['posterior'],[Fraction(1,4),Fraction(3,4)])
        self.assertEqual(result['observation_evidence_mass'],1)
        self.assertEqual(result['samples'],20)
        self.assertIsNone(result['native_infoset_ev'])

    def test_preflop_belief_continues_through_real_postflop(self):
        result=belief_value(self.native,NativeGame([4,4]),[48,49],
            [([0,1],Fraction(1,2)),([2,3],Fraction(1,2))],[],[],
            lambda node:{1:Fraction(1)},samples_per_deal=100,seed=17)
        self.assertGreater(result['sample_mean_values'][0],0)
        self.assertEqual(sum(result['sample_mean_values']),0)
        self.assertEqual(result['samples'],200)

    def test_belief_zero_reach_and_budget(self):
        args=(self.native,NativeGame([20,20]),[48,49],[([0,1],Fraction(1))],[],[1])
        result=belief_value(*args,lambda node:{0:Fraction(1)},samples_per_deal=10,seed=17)
        self.assertIsNone(result['sample_mean_values']);self.assertEqual(result['samples'],0)
        with self.assertRaises(ValueError):
            belief_value(*args,lambda node:{1:Fraction(1)},samples_per_deal=10,seed=17,max_total_samples=1)

    def test_belief_rejects_omniscient_hero_policy(self):
        def omniscient(node):
            return {0 if node.audit()['holes'][1][0]==0 else 1:Fraction(1)}
        with self.assertRaisesRegex(ValueError,'hero policy differs'):
            belief_value(self.native,NativeGame([20,20]),[48,49],
                [([0,1],Fraction(1,2)),([2,3],Fraction(1,2))],[],[],omniscient,
                samples_per_deal=1,seed=17)

    def test_belief_posterior_uses_action_likelihood(self):
        def policy(node):
            if node.current_player()==1:
                if 0 not in node.legal_actions():return {1:Fraction(1)}
                p=Fraction(1,4) if node.audit()['holes'][1][0]==0 else Fraction(3,4)
                return {0:1-p,1:p}
            if not node.audit()['history']:return {8:Fraction(1)}
            return {1:Fraction(1)}
        # Hero raises; opponent call is more likely for the second supplied hand.
        result=belief_value(self.native,NativeGame([20,20]),[48,49],
            [([0,1],Fraction(1,2)),([2,3],Fraction(1,2))],[],[8,1],policy,
            samples_per_deal=2,seed=17)
        self.assertEqual(result['posterior'],[Fraction(1,4),Fraction(3,4)])
        self.assertEqual(result['observation_evidence_mass'],Fraction(1,2))

    def test_fourbet_response_actions_share_prefix_belief(self):
        prefix=[1,8,20,44]
        def policy(node):
            history=node.audit()['history']
            return {prefix[len(history)] if len(history)<len(prefix) else 1:Fraction(1)}
        result=action_values(self.native,NativeGame([200,200]),[48,49],
            [([0,1],Fraction(1,2)),([2,3],Fraction(1,2))],[],prefix,[0,1,92],policy,
            samples_per_deal=50,seed=17)
        fold=result['actions'][0]
        self.assertEqual(fold['sample_mean_values'],[Fraction(-18),Fraction(18)])
        self.assertEqual(fold['posterior'],[Fraction(1,2),Fraction(1,2)])
        for row in result['actions'].values():
            self.assertEqual(row['observation_evidence_mass'],1)
            self.assertEqual(sum(row['sample_mean_values']),0)
        self.assertEqual(result['samples'],300)

    def test_action_values_reject_illegal_intervention(self):
        with self.assertRaises(ValueError):
            action_values(self.native,NativeGame([20,20]),[48,49],
                [([0,1],Fraction(1))],[],[],[2],lambda node:{1:Fraction(1)},
                samples_per_deal=1,seed=17)

    def test_mixed_policy_matches_hand_derived_river_ev(self):
        state=self.state()
        for action in [1,1,8,17,26,1,1,32,1,1,41,6]:
            state.apply_action(action)
        # AA beats22 on this river: folding loses2 chips; calling wins6.
        policy=lambda node:{0:Fraction(3,4),1:Fraction(1,4)}
        exact=exact_policy_value(state,policy)
        self.assertEqual(exact['values'],[Fraction(0),Fraction(0)])
        result=policy_value(state,policy,samples=2000,seed=17)
        self.assertLess(abs(result['values'][0]),Fraction(1,4))
        for lo,hi in result['simultaneous_chip_intervals']:
            self.assertLessEqual(lo,0);self.assertGreaterEqual(hi,0)

    def test_confidence_width_scales_with_inverse_square_root_samples(self):
        policy=lambda node:{0:Fraction(1)}
        a=policy_value(self.state(),policy,samples=100,seed=1)
        b=policy_value(self.state(),policy,samples=400,seed=1)
        width=lambda report:report['simultaneous_chip_intervals'][0][1]-report['simultaneous_chip_intervals'][0][0]
        self.assertAlmostEqual(width(a)/width(b),2)

    def test_actual_native_snapshot_missing_rows_fail_closed(self):
        from itertools import combinations
        from gto.native.infoset_export import PolicySnapshot
        game=NativeGame([4,4]);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(200):solver.run_iteration()
        snapshot=PolicySnapshot.from_solver(self.native,solver)
        keys=set(solver.keys())
        for pair in combinations(range(52),2):
            others=[c for c in range(52) if c not in pair][:2]
            state=decision(self.native,game,[],cards=list(pair)+others)
            if state.information_state_string(0) not in keys:break
        else:self.fail('small training unexpectedly covered every root combination')
        with self.assertRaisesRegex(ValueError,'snapshot row missing'):
            policy_value(state,snapshot,samples=1,seed=17)

    def test_mutating_policy_and_invalid_numeric_controls_rejected(self):
        def mutating(node):
            node.apply_action(0)
            return {0:Fraction(1)}
        with self.assertRaisesRegex(ValueError,'mutated'):
            policy_value(self.state(),mutating,samples=1,seed=1)
        for kwargs in ({'samples':True},{'samples':0},{'samples':100001},
                {'seed':True},{'confidence':float('nan')},{'confidence':1},
                {'max_steps':True}):
            args={'samples':1,'seed':1,**kwargs}
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                policy_value(self.state(),lambda node:{0:Fraction(1)},**args)


if __name__=='__main__':unittest.main()

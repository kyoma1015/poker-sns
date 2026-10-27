"""Actual native2..9-player joint-support/reach/EV checks; not convergence."""
from fractions import Fraction as F
from itertools import permutations
import importlib
import math
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.joint_support import condition_joint_support,product_support
from gto.native.joint_reach import joint_reach,joint_value,joint_actions
from gto.native.training import NativeGame


class Joint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR'])
        cls.native=importlib.import_module('pokerid_g12')

    def test_card_removal_accounts_hero_cross_seat_and_board_mass(self):
        deals=[([[0,1],[2,3]],F(1,4)),([[48,1],[2,3]],F(1,4)),
               ([[0,1],[1,3]],F(1,4)),([[0,1],[20,3]],F(1,4))]
        r=condition_joint_support(3,[48,49],deals,[20,21,22])
        self.assertEqual(r['compatible_prior_mass'],F(1,4))
        self.assertEqual(r['removed_prior_mass'],F(3,4))
        self.assertEqual(r['deals'],[(((48,49),(0,1),(2,3)),F(1))])
        self.assertFalse(r['support_complete'])

    def test_ordered_deals_are_distinct_native_information_keys(self):
        r=condition_joint_support(2,[48,49],[([[0,1]],F(1,2)),([[1,0]],F(1,2))])
        self.assertEqual(r['positive_compatible_deals'],2)
        self.assertEqual(r['uniform_ordered_support_fraction'],F(2,2450))

    def test_full_heads_up_ordered_card_support_count(self):
        available=[c for c in range(52) if c not in (48,49)]
        deals=[([cards],F(1,2450)) for cards in permutations(available,2)]
        r=condition_joint_support(2,[48,49],deals,max_deals=2450)
        self.assertTrue(r['support_complete'])
        self.assertEqual(r['uniform_ordered_support_fraction'],1)
        self.assertFalse(r['equilibrium_verified'])

    def test_independent_range_product_conditions_shared_blockers(self):
        ranges={1:[([0,1],F(1,2)),([2,3],F(1,2))],2:[([0,4],F(1,2)),([5,6],F(1,2))]}
        r=product_support(3,[48,49],ranges)
        self.assertEqual(r['compatible_prior_mass'],F(3,4))
        self.assertEqual([p for _,p in r['deals']],[F(1,3)]*3)
        with self.assertRaises(ValueError):product_support(3,[48,49],ranges,max_candidates=3)
        with self.assertRaises(ValueError):product_support(3,[48,49],ranges,max_deals=2)

    def test_invalid_and_duplicate_joint_priors_rejected(self):
        for deals in ([([[0,1]],F(1,2)),([[0,1]],F(1,2))],
                      [([[0,0]],F(1))],[([[0,1]],1.0)],[([[0,1]],F(1,2))]):
            with self.subTest(deals=deals),self.assertRaises(ValueError):
                condition_joint_support(2,[48,49],deals)

    def test_all_blocked_support_remains_explicitly_unavailable(self):
        r=joint_value(self.native,NativeGame([20]*3),[48,49],
            [([[0,1],[1,2]],F(1))],[],[],lambda n:{1:F(1)},samples_per_deal=3,seed=17)
        self.assertIsNone(r['sample_mean_values']);self.assertIsNone(r['posterior'])
        self.assertEqual(r['samples'],0);self.assertFalse(r['history_validated'])

    def test_actual_three_player_action_likelihood_posterior(self):
        def policy(node):
            if node.current_player()==2:
                p=F(1,4) if node.audit()['holes'][2][0]==4 else F(3,4)
                return {8:p,0:1-p}
            return {1:F(1,2),0:F(1,2)}
        deals=[([[0,1],[4,5]],F(1,2)),([[0,1],[8,9]],F(1,2))]
        r=joint_reach(self.native,NativeGame([200]*3),[48,49],deals,[],[8,1],policy,hero_seat=1)
        self.assertEqual(r['posterior'],[F(1,4),F(3,4)])
        self.assertEqual(r['observation_evidence_mass'],F(1,4))
        self.assertEqual(r['reach_records'][0]['strategy_reach'],[F(1,2),F(1),F(1,4)])
        self.assertEqual(r['reach_records'][0]['uniform_private_deal_probability'],F(1,math.perm(52,6)))

    def test_per_player_reach_and_hero_excluded_reach_are_separate(self):
        def policy(node):
            length=len(node.audit()['history'])
            return ({8:F(1,2),0:F(1,2)},{1:F(1,3),0:F(2,3)},
                    {20:F(1,4),1:F(3,4)},{1:F(1,5),0:F(4,5)})[length]
        r=joint_reach(self.native,NativeGame([200]*3),[48,49],
            [([[0,1],[4,5]],F(1))],[],[8,1,20,1],policy)
        self.assertEqual(r['reach_records'][0]['strategy_reach'],[F(1,3),F(1,4),F(1,10)])
        self.assertEqual(r['observation_evidence_mass'],F(1,120))
        self.assertEqual(r['hero_excluded_evidence_mass'],F(1,40))

    def test_public_chance_is_replayed_with_multiway_remaining_deck(self):
        r=joint_reach(self.native,NativeGame([20]*3),[48,49],
            [([[0,1],[4,5]],F(1))],[20,21,22],[1,1,1,20,21,22],lambda n:{1:F(1)})
        self.assertEqual(r['reach_records'][0]['chance_reach'],F(1,46*45*44))
        self.assertEqual(r['observation_evidence_mass'],F(1,46*45*44))

    def test_every_queried_opponent_must_use_own_infoset(self):
        def omniscient(node):
            if node.current_player()!=1:return {1:F(1)}
            p=F(1,4) if node.audit()['holes'][2][0]==4 else F(3,4)
            return {1:p,6:1-p}
        with self.assertRaisesRegex(ValueError,'identical queried actor infoset'):
            joint_reach(self.native,NativeGame([20]*3),[48,49],
                [([[0,1],[4,5]],F(1,2)),([[0,1],[8,9]],F(1,2))],[],[1,1,1],omniscient)

    def test_all_table_sizes_and_hero_seats_preserve_real_deal_assignment(self):
        for players in range(2,10):
            hands=[[2*i,2*i+1] for i in range(players-1)]
            for hero in range(players):
                r=joint_reach(self.native,NativeGame([20]*players),[48,49],[(hands,F(1))],[],[],
                    lambda n:{1:F(1)},hero_seat=hero)
                self.assertEqual(r['reach_records'][0]['hands'][hero],[48,49])
                self.assertEqual(r['posterior'],[F(1)])
                self.assertEqual(len(r['reach_records'][0]['strategy_reach']),players)

    def test_multiway_sample_ev_conserves_chips_with_ante_and_unequal_stacks(self):
        for players in range(2,10):
            hands=[[2*i,2*i+1] for i in range(players-1)]
            for ante in (0,2):
                r=joint_value(self.native,NativeGame([2*i+2 for i in range(players)],bba=ante),
                    [48,49],[(hands,F(1))],[],[],lambda n:{0:F(1)},samples_per_deal=3,seed=17)
                self.assertEqual(r['sample_mean_values'],[F(-1),F(1)]+[F(0)]*(players-2))
                self.assertEqual(sum(r['sample_mean_values']),-r['mean_rake'])

    def test_three_player_fourbet_response_interventions_share_true_prefix(self):
        prefix=[8,20,44]
        def policy(node):
            length=len(node.audit()['history'])
            return {prefix[length] if length<len(prefix) else 1:F(1)}
        r=joint_actions(self.native,NativeGame([200]*3),[48,49],
            [([[0,1],[4,5]],F(1))],[],prefix,[0,1,92],policy,
            hero_seat=2,samples_per_deal=10,seed=17)
        self.assertEqual(r['actions'][0]['sample_mean_values'][2],F(-6))
        self.assertEqual(r['reach']['observation_evidence_mass'],1)
        self.assertEqual(r['samples'],30)
        for row in r['actions'].values():self.assertEqual(sum(row['sample_mean_values']),-row['mean_rake'])

    def test_joint_budgets_and_illegal_interventions_fail_closed(self):
        args=(self.native,NativeGame([200]*3),[48,49],[([[0,1],[4,5]],F(1))],[],[])
        with self.assertRaises(ValueError):joint_value(*args,lambda n:{1:F(1)},samples_per_deal=2,seed=17,max_total_samples=1)
        with self.assertRaises(ValueError):joint_actions(*args,[2],lambda n:{1:F(1)},hero_seat=2,samples_per_deal=1,seed=17)

    def test_actual_learned_native_row_determines_prefix_reach(self):
        import json
        from gto.native.infoset_export import PolicySnapshot
        from gto.native.preflop import decision
        game=NativeGame([4]*3);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(400):solver.run_iteration()
        key=next(key for key in solver.keys() if json.loads(key)['seat']==2
            and not json.loads(key)['betting_history'] and not json.loads(key)['board']
            and sum(solver.row(key)['average'])>0)
        hero=json.loads(key)['hand'];remaining=[c for c in range(52) if c not in hero]
        hands=[remaining[:2],remaining[2:4]];full=hands+[hero]
        state=decision(self.native,game,[],cards=[c for hand in full for c in hand])
        snapshot=PolicySnapshot.from_solver(self.native,solver);row=snapshot(state)
        action=next(a for a,p in row.items() if p>0)
        result=joint_reach(self.native,game,hero,[(hands,F(1))],[],[action],snapshot,hero_seat=2)
        self.assertEqual(result['observation_evidence_mass'],row[action])
        self.assertEqual(result['reach_records'][0]['strategy_reach'],[F(1),F(1),row[action]])
        self.assertIsNone(result['native_infoset_ev'])

    def test_three_way_turn_ev_side_pots_rake_and_exact_oracle(self):
        from gto.native.poker_oracle import exact_policy_value
        prefix=[1,12,1];board=[8,17,26,32];history=prefix+board
        def policy(node):
            length=len(node.audit()['history'])
            return {prefix[length] if length<len(prefix) else 1:F(1)}
        for rake in (0,1):
            game=NativeGame([10,6,2],rake_num=rake,rake_den=10 if rake else 1)
            state=self.native.NativeState(game)
            for card in [48,49,44,45,40,41]+history:state.apply_action(card)
            exact=exact_policy_value(state,lambda n:{1:F(1)},max_nodes=1000)
            if not rake:self.assertEqual(exact['values'],[F(148,21),F(-112,21),F(-12,7)])
            result=joint_value(self.native,game,[48,49],[([[44,45],[40,41]],F(1))],board,history,
                policy,samples_per_deal=2000,seed=17)
            self.assertEqual(result['mean_rake'],rake)
            for p,value in enumerate(exact['values']):
                self.assertLess(abs(result['sample_mean_values'][p]-value),1)
                lo,hi=result['simultaneous_chip_intervals'][p]
                self.assertLessEqual(lo,float(value));self.assertGreaterEqual(hi,float(value))
            self.assertEqual(sum(result['sample_mean_values']),-rake)


if __name__=='__main__':unittest.main()

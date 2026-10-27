"""Real native continuation bounds, oracle comparisons and learned coverage."""
from fractions import Fraction as F
import importlib,json,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.preflop import decision
from gto.native.full_game_bounds import world_bounds
from gto.native.ordinary_study import context_coverage,evaluate_rfi
from gto.native.infoset_export import PolicySnapshot
from gto.native.poker_oracle import exact_policy_value

class FullGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_g12')
    def river(self):
        game=NativeGame([4,4]);state=decision(self.native,game,[],cards=[48,49,0,1]);cards=iter([8,17,26,32,35])
        while state.audit()['round']<3 or state.is_chance_node():
            state.apply_action(next(cards) if state.is_chance_node() else 1)
        self.assertFalse(state.is_chance_node());return state
    def test_full_river_continuation_matches_exact_profile_oracle(self):
        state=self.river();policy=lambda n:{1:F(1)}
        exact=exact_policy_value(state,policy)
        result=world_bounds(state,policy,state.audit()['deck'],[4,4],max_nodes=10000)
        self.assertEqual(result['profile_intervals_chips'],[(v,v) for v in exact['values']])
        self.assertEqual(exact['values'],[F(2),F(-2)])
        self.assertEqual(result['clairvoyant_response_upper_chips'],[F(4),F(-2)])
        self.assertFalse(result['full_game_convergence_verified'])
    def test_real_board_chance_paths_are_not_replaced_by_showdown(self):
        game=NativeGame([4,4]);state=decision(self.native,game,[1,1],cards=[48,49,0,1])
        deck=state.audit()['deck'];value=world_bounds(state,lambda n:{1:F(1)},deck,[4,4],max_nodes=1000)
        self.assertGreater(value['traversals'][0]['terminals'],0)
        self.assertGreater(value['traversals'][0]['nodes'],5)
    def test_unknown_policy_and_budget_cut_are_intervals_not_filled_policy(self):
        state=self.river();policy=PolicySnapshot({'unrelated':{1:F(1)}})
        for budget in (1,64):
            result=world_bounds(state,policy,state.audit()['deck'],[4,4],max_nodes=budget)
            self.assertLessEqual(result['profile_intervals_chips'][0][0],2)
            self.assertGreaterEqual(result['profile_intervals_chips'][0][1],2)
            self.assertGreaterEqual(result['clairvoyant_response_upper_chips'][0],4)
            self.assertGreater(sum(t['unknown']+t['cutoffs'] for t in result['traversals']),0)
    def test_full_remaining_deck_required(self):
        state=self.river();deck=state.audit()['deck']
        for bad in (deck[:-1],deck+[deck[0]],[True]+deck[1:]):
            with self.assertRaises(ValueError):world_bounds(state,lambda n:{1:F(1)},bad,[4,4])
    def test_owner_zero_pseudocount_rows_do_not_enter_frozen_policy(self):
        game=NativeGame([100,100]);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(20):solver.run_iteration()
        keys=solver.keys();unknown=[k for k in keys if solver.row(k)['updates']==0]
        self.assertTrue(unknown);policy=PolicySnapshot.from_solver(self.native,solver)
        for key in unknown:self.assertNotIn(key,policy._rows)
        self.assertTrue(policy._rows)
    def test_ordinary_partial_coverage_preserves_null_and_no_later_uniform_reach(self):
        game=NativeGame([100,100]);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(20):solver.run_iteration()
        for history,stage in (([],'rfi'),([7],'vs_open'),([7,20],'vs_3bet'),([7,20,44],'vs_4bet')):
            result=context_coverage(self.native,solver,game,history)
            self.assertEqual(result['stage'],stage);self.assertEqual(len(result['hands']),169)
            self.assertFalse(result['full_game_convergence_verified'])
            self.assertTrue(all(h['ev_bb'] is None for h in result['hands'].values()))
            self.assertEqual(result['complete_frequency_classes'],0)
    def test_bad_evaluation_schedule_rejected(self):
        for samples in (True,0,10001):
            with self.assertRaises(ValueError):evaluate_rfi(self.native,NativeGame([100,100]),None,samples_per_class=samples)

if __name__=='__main__':unittest.main()

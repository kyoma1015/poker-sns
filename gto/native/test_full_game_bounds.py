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
        game=NativeGame([4,4]);state=decision(self.native,game,[],cards=[48,49,0,1])
        for action in (1,1):state.apply_action(action)
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
    def test_reached_class_frequencies_match_full_ordered_opponent_enumeration(self):
        from gto.native.hu_preflop_reach import reached_classes,PAIRS
        from gto.native.hand169_bridge import context_of
        game=NativeGame([100,100]);contexts=[];rows={}
        for prefix in ([],[7]):
            node=decision(self.native,game,prefix);ctx=context_of(node.information_state_string(node.current_player()))
            contexts.append(ctx);actions=node.legal_actions()
            for pair in PAIRS:
                key=json.dumps(dict(ctx,hand=list(pair)),sort_keys=True,separators=(',',':'))
                probability=(.75 if 0 in pair else .25) if not prefix else float(pair[0]==0)
                values=[0.0]*len(actions)
                if not prefix:values[actions.index(7)]=probability;values[actions.index(0)]=1-probability
                else:values[actions.index(0)]=probability;values[actions.index(1)]=1-probability
                rows[key]={'actions':actions,'average':values,'updates':1}
        class ExplicitRows:
            def keys(self):return list(rows)
            def row(self,key):return rows[key]
        result=reached_classes(self.native,ExplicitRows(),game,[7])
        self.assertEqual(result['complete_frequency_classes'],169)
        # Independent2450-opponent enumeration per ordered22hero hand. This
        # deliberately exercises card removal and order-dependent target policy.
        numerator=denominator=F(0)
        for hero in [p for p in PAIRS if p[0]//4==0 and p[1]//4==0]:
            likelihood=sum((F(3,4) if 0 in opponent else F(1,4)
                for opponent in PAIRS if not set(hero)&set(opponent)),F(0))
            denominator+=likelihood;numerator+=likelihood*int(hero[0]==0)
        actions=decision(self.native,game,[7]).legal_actions()
        actual=result['hands']['22']['frequencies'][actions.index(0)]
        self.assertAlmostEqual(actual,float(numerator/denominator),places=14)
        for hand in result['hands'].values():self.assertAlmostEqual(sum(hand['frequencies']),1)
        self.assertFalse(result['full_game_convergence_verified'])

    def test_missing_learned_prefix_cannot_create_posterior_range(self):
        from gto.native.hu_preflop_reach import reached_classes
        game=NativeGame([100,100]);solver=self.native.Solver(game,.6,17,True,True,.1)
        for _ in range(20):solver.run_iteration()
        result=reached_classes(self.native,solver,game,[7])
        self.assertEqual(result['status'],'opponent_prefix_policy_missing')
        self.assertIsNone(result['hands']);self.assertEqual(result['complete_frequency_classes'],0)

    def test_bad_evaluation_schedule_rejected(self):
        for samples in (True,0,10001):
            with self.assertRaises(ValueError):evaluate_rfi(self.native,NativeGame([100,100]),None,samples_per_class=samples)

if __name__=='__main__':unittest.main()

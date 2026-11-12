from fractions import Fraction as F
import importlib,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.belief_observation import compare_hero_actions
class Actions(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.n=importlib.import_module('pokerid_g12')
 def history(self):return [1,1,1,8,17,1,1,26,1,1,35,1]
 def policy(self,s):return {0:F(1)} if 0 in s.legal_actions() else {1:F(1)}
 def runvalue(self,**kw):
  args=dict(native=self.n,game=NativeGame([4,4]),hero_cards=[0,5],deals=[([48,49],F(1,4)),([40,45],F(3,4))],public_cards=[1,8,17,26,35],history=self.history(),actions=[1,4],policy=lambda s:{1:F(1)} if not s.audit()['board'] or s.audit()['round']<3 or s.current_player()==0 else self.policy(s))
  args.update(kw);return compare_hero_actions(**args)
 def test_exact_same_posterior_for_both_interventions(self):
  r=self.runvalue();self.assertEqual(r['posterior'],[F(1,4),F(3,4)]);self.assertEqual(r['action_values'],{1:[F(1),F(-1)],4:[F(2),F(-2)]});self.assertIsNone(r['hand169_ev'])
 def test_intervention_not_scaled_by_target_policy(self):
  def p(s):
   if s.audit()['round']==3 and s.current_player()==0:return {4:F(1)}
   return self.policy(s) if s.audit()['round']==3 else {1:F(1)}
  self.assertEqual(self.runvalue(policy=p)['action_values'][1],[F(1),F(-1)])
 def test_observation_mass_and_counterfactual_distinct(self):
  r=self.runvalue();self.assertEqual(r['observation_evidence_mass'],F(1,48*47*46*45*44));self.assertEqual(r['hero_counterfactual_mass'],r['observation_evidence_mass'])
 def test_illegal_duplicate_empty_bool_actions_refused(self):
  for actions in [[0],[1,1],[],[True],[99]]:
   with self.subTest(actions=actions),self.assertRaises(ValueError):self.runvalue(actions=actions)
 def test_action_and_total_nodes_bound(self):
  with self.assertRaises(ValueError):self.runvalue(max_actions=1)
  with self.assertRaises(ValueError):self.runvalue(max_nodes=1)
 def test_only_common_hero_decision_is_accepted(self):
  with self.assertRaises(ValueError):self.runvalue(history=self.history()[:-1])
  with self.assertRaises(ValueError):self.runvalue(history=self.history()+[1])
 def test_board_mismatch_refused(self):
  with self.assertRaises(ValueError):self.runvalue(public_cards=[1,8,17,26])
 def test_zero_prefix_reach_values_null(self):
  def p(s):return {0:F(1)} if 0 in s.legal_actions() else {1:F(1)}
  r=self.runvalue(policy=p);self.assertEqual(r['observation_evidence_mass'],0);self.assertIsNone(r['posterior']);self.assertEqual(r['action_values'],{1:None,4:None});self.assertGreater(r['hero_counterfactual_mass'],0)
 def test_hidden_information_dependent_prefix_policy_refused(self):
  def p(s):
   if s.current_player()==0 and s.audit()['round']==0:return {1:F(1)} if s.audit()['holes'][1][0]==48 else {0:F(1)}
   return {1:F(1)}
  with self.assertRaises(ValueError):self.runvalue(policy=p)
 def test_allblocked_support_null_unvalidated(self):
  r=self.runvalue(public_cards=[48,40,17],history=[1,1,48,40,17]);self.assertIsNone(r['action_values']);self.assertFalse(r['history_validated'])
 def test_opponent_call_changes_action_values_with_exact_weights(self):
  r=self.runvalue(deals=[([48,49],F(3,4)),([40,45],F(1,4))],policy=lambda s:{1:F(1)})
  self.assertEqual(r['action_values'],{1:[F(-1),F(1)],4:[F(-2),F(2)]})
 def test_exact_aggregate_budget_and_action_order_determinism(self):
  a=self.runvalue(max_nodes=6);b=self.runvalue(actions=[4,1],max_nodes=6)
  self.assertEqual(a['action_values'],b['action_values']);self.assertEqual(a['nodes'],6);self.assertEqual(a['action_nodes'],{1:2,4:4})
  with self.assertRaises(ValueError):self.runvalue(max_nodes=5)
 def test_public_conditioned_support_provenance_kept(self):
  r=self.runvalue();self.assertFalse(r['support_complete']);self.assertEqual(r['compatible_prior_mass'],1);self.assertEqual(r['removed_prior_mass'],0);self.assertEqual(len(r['hero_information_sha256']),64)

if __name__=='__main__':unittest.main()

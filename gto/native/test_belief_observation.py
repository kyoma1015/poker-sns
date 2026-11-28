from fractions import Fraction as F
import importlib,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.belief_observation import condition_public_cards,infoset_consistent_policy,evaluate_observation
class Observation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.n=importlib.import_module('pokerid_g12')
 def deals(self):return [([48,49],F(1,4)),([40,45],F(3,4))]
 def state(self,cards):
  s=self.n.NativeState(NativeGame([4,4]))
  for a in [0,5]+cards:s.apply_action(a)
  return s
 def test_support_mass_conservation_and_exact_conditioning(self):
  r=condition_public_cards([0,5],self.deals(),[48,8,17])
  self.assertEqual(r['compatible_prior_mass'],F(3,4));self.assertEqual(r['removed_prior_mass'],F(1,4));self.assertEqual(r['deals'],[([40,45],F(1))])
 def test_all_blocked_is_unknown_not_uniform(self):
  r=condition_public_cards([0,5],self.deals(),[48,40,17]);self.assertEqual(r['deals'],[]);self.assertEqual(r['compatible_prior_mass'],0)
 def test_invalid_board_and_private_support(self):
  for board in [[0],[8,8],[True],[52],list(range(6))]:
   with self.assertRaises(ValueError):condition_public_cards([0,5],self.deals(),board)
  for deals in [[],[([48,49],.5)],[([48,49],F(1,2))],[([48,49],F(1,2)),([49,48],F(1,2))]]:
   with self.assertRaises(ValueError):condition_public_cards([0,5],deals,[])
 def test_cap_checked_before_expansion(self):
  with self.assertRaises(ValueError):condition_public_cards([0,5],self.deals(),[],max_deals=1)
 def test_hero_infoset_hidden_card_policy_leak_refuses(self):
  def spy(s):return {0:F(1)} if s.audit()['holes'][1][0]==48 else {1:F(1)}
  p=infoset_consistent_policy(spy);a=self.state([48,49]);b=self.state([40,45])
  self.assertEqual(a.information_state_string(0),b.information_state_string(0));p(a)
  with self.assertRaises(ValueError):p(b)
 def test_consistent_hero_policy_and_copied_results(self):
  p=infoset_consistent_policy(lambda s:{1:F(1)});x=p(self.state([48,49]));x.clear();self.assertEqual(p(self.state([40,45])),{1:F(1)})
 def test_observation_river_exact_ev_and_mass(self):
  r=evaluate_observation(self.n,NativeGame([4,4]),[0,5],self.deals(),[1,8,17,26,35],[1,1,1,8,17,1,1,26,1,1,35,1,1],lambda s:{1:F(1)})
  self.assertEqual(r['conditional_ev'],[F(1),F(-1)]);self.assertEqual(r['observation_evidence_mass'],F(1,48*47*46*45*44));self.assertIsNone(r['hand169_ev'])
 def test_observation_filtered_mass_not_double_counted(self):
  state=self.state([40,45])
  for action in [1,1,48,8,17]:state.apply_action(action)
  shove=max(state.legal_actions());aggressor=state.current_player()
  def policy(node):
   if not node.audit()['board']:return {1:F(1)}
   return {max(node.legal_actions()):F(1)} if node.current_player()==aggressor else {0:F(1)}
  r=evaluate_observation(self.n,NativeGame([4,4]),[0,5],self.deals(),[48,8,17],[1,1,48,8,17,shove,0],policy)
  self.assertEqual(r['compatible_prior_mass'],F(3,4));self.assertEqual(r['observation_evidence_mass'],F(3,4*48*47*46))
  self.assertEqual(r['posterior'],[F(1)])
 def test_history_board_mismatch_refuses(self):
  with self.assertRaises(ValueError):evaluate_observation(self.n,NativeGame([4,4]),[0,5],self.deals(),[8,17,26],[0],lambda s:{0:F(1)})
 def test_zero_support_value_null(self):
  r=evaluate_observation(self.n,NativeGame([4,4]),[0,5],self.deals(),[48,40,17],[1,1,48,40,17],lambda s:{1:F(1)})
  self.assertIsNone(r['conditional_ev']);self.assertEqual(r['observation_evidence_mass'],0)
 def test_zero_weight_representation_is_same_hero_policy(self):
  calls=[0]
  def p(node):
   calls[0]+=1
   return {1:F(1),0:F(0)} if calls[0]==1 else {1:F(1)}
  checked=infoset_consistent_policy(p);checked(self.state([48,49]));checked(self.state([40,45]))
 def test_infoset_limit_and_invalid_parameters(self):
  with self.assertRaises(ValueError):infoset_consistent_policy(lambda s:{1:F(1)},player=True)
  with self.assertRaises(ValueError):infoset_consistent_policy(lambda s:{1:F(1)},max_infosets=0)
  checked=infoset_consistent_policy(lambda s:{1:F(1)},max_infosets=1)
  state=self.state([48,49]);checked(state)
  for a in [1,1,8,17,26,1]:state.apply_action(a)
  self.assertEqual(state.current_player(),0)
  with self.assertRaises(ValueError):checked(state)
 def test_empty_observation_and_zero_prior_support(self):
  r=condition_public_cards([0,5],[([48,49],F(0)),([40,45],F(1))],[48])
  self.assertEqual(r['compatible_prior_mass'],1);self.assertEqual(r['removed_prior_mass'],0)
  r=condition_public_cards([0,5],self.deals(),[]);self.assertEqual(r['compatible_prior_mass'],1)

if __name__=='__main__':unittest.main()

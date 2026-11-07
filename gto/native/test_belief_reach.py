"""Exact finite conditional opponent support, never a full-poker convergence proof."""
from fractions import Fraction as F
import importlib,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.history_reach import bounded_belief_value,immutable_average_policy
class Belief(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.n=importlib.import_module('pokerid_g12')
 def runvalue(self,deals=None,history=None,policy=None,**kw):
  return bounded_belief_value(self.n,NativeGame([4,4]),[0,5],deals or [([48,49],F(1,4)),([44,45],F(3,4))],history if history is not None else [0],policy or (lambda s:{0:F(1)}),**kw)
 def test_fold_ev_and_belief_mass(self):
  r=self.runvalue();self.assertEqual(r['conditional_ev'],[F(-1),F(1)]);self.assertEqual(r['evidence_mass'],1);self.assertEqual(r['posterior'],[F(1,4),F(3,4)]);self.assertIsNone(r['native_infoset_ev'])
 def test_strategy_bayes_and_counterfactual_separate(self):
  def p(s):return {0:F(1,4) if s.audit()['holes'][1][0]==48 else F(1,2),1:F(3,4) if s.audit()['holes'][1][0]==48 else F(1,2)}
  r=self.runvalue(policy=p,counterfactual_player=0)
  self.assertEqual(r['evidence_mass'],F(7,16));self.assertEqual(r['posterior'],[F(1,7),F(6,7)]);self.assertEqual(r['counterfactual_mass'],1)
 def test_zero_observation_unknown(self):
  r=self.runvalue(policy=lambda s:{1:F(1)});self.assertIsNone(r['conditional_ev']);self.assertIsNone(r['posterior'])
 def test_illegal_and_duplicate_private_cards(self):
  for deals in [[([0,49],F(1))],[([48,48],F(1))],[([48,49],F(1,2)),([49,48],F(1,2))],[([True,49],F(1))]]:
   with self.subTest(deals=deals),self.assertRaises(ValueError):self.runvalue(deals=deals)
 def test_mass_and_bounds_refuse(self):
  for deals in [[([48,49],F(1,2))],[([48,49],.5)],[([48,49],F(-1)),([44,45],F(2))]]:
   with self.assertRaises(ValueError):self.runvalue(deals=deals)
  with self.assertRaises(ValueError):self.runvalue(max_deals=1)
  with self.assertRaises(ValueError):self.runvalue(max_nodes=1)
 def test_legal_history_and_unknown_policy_refuse(self):
  with self.assertRaises(ValueError):self.runvalue(history=[99])
  with self.assertRaises(ValueError):self.runvalue(policy=lambda s:{999:F(1)})
 def test_snapshot_survives_later_solver_training(self):
  g=NativeGame([4,4]);s=self.n.Solver(g,.6,17,True,True,.1)
  for _ in range(20000):s.run_iteration()
  p=immutable_average_policy(self.n,s);node=self.n.NativeState(g)
  with self.assertRaises(ValueError):immutable_average_policy(self.n,s,max_rows=1)
  for a in [0,5,48,49]:node.apply_action(a)
  before=p(node);s.run_iteration();self.assertEqual(p(node),before);before.clear();self.assertTrue(p(node))
 def test_snapshot_requires_observed_rows(self):
  g=NativeGame([4,4]);s=self.n.Solver(g,.6,17,True,True,.1);p=immutable_average_policy(self.n,s);node=self.n.NativeState(g)
  for a in [0,5,48,49]:node.apply_action(a)
  with self.assertRaises(ValueError):p(node)
 def test_public_card_blocker_inconsistent_support_refuses(self):
  with self.assertRaises(ValueError):self.runvalue(history=[1,1,48],policy=lambda s:{1:F(1)})
 def test_multiplayer_not_silently_approximated(self):
  with self.assertRaises(ValueError):bounded_belief_value(self.n,NativeGame([4,4,4]),[0,5],[([48,49],F(1))],[0],lambda s:{0:F(1)})
 def test_chance_separate_from_prior_and_zero_mass(self):
  r=self.runvalue(history=[1,1,8,17,26],policy=lambda s:{0 if 0 in s.legal_actions() else 1:F(1)})
  self.assertEqual(r['support'][0]['chance_reach'],F(1,48*47*46))
  self.assertIsNone(r['posterior'])
 def test_distinct_showdown_ev_exact_weighted_belief(self):
  r=self.runvalue(deals=[([48,49],F(1,4)),([40,45],F(3,4))],history=[1,1,1,8,17,1,1,26,1,1,35,1,1],policy=lambda s:{1:F(1)})
  self.assertEqual(r['support'][0]['values'],[F(-2),F(2)])
  self.assertEqual(r['support'][1]['values'],[F(2),F(-2)])
  self.assertEqual(r['conditional_ev'],[F(1),F(-1)])
  self.assertEqual(r['posterior'],[F(1,4),F(3,4)])
  self.assertEqual(r['evidence_mass'],F(1,48*47*46*45*44))
 def test_checkpoint_snapshot_determinism(self):
  import tempfile
  from gto.native.training import train_batch
  g=NativeGame([4,4]);a=self.n.Solver(g,.6,17,True,True,.1);b=self.n.Solver(g,.6,17,True,True,.1)
  with tempfile.TemporaryDirectory() as d:
   train_batch(a,g,4000,Path(d)/'all');train_batch(b,g,2000,Path(d)/'first')
   c=self.n.Solver(g,.6,17,True,True,.1);train_batch(c,g,2000,Path(d)/'second',resume=Path(d)/'first')
   node=self.n.NativeState(g)
   for x in [0,5,48,49]:node.apply_action(x)
   self.assertEqual(immutable_average_policy(self.n,a)(node),immutable_average_policy(self.n,c)(node))
   self.assertEqual(a.rng_state(),c.rng_state())

if __name__=='__main__':unittest.main()

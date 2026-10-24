"""Additional actual-native EV-path and nonmutation integration checks."""
from fractions import Fraction
import importlib,os
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from gto.native.training import NativeGame
from gto.native.history_reach import native_average_policy,evaluate_history,trace_history
class HistoryEV(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_g12')
 def test_learned_native_policy_reaches_exact_fold_ev_without_rng_change(self):
  g=NativeGame([4,4]);solver=self.native.Solver(g,.6,17,True,True,.1)
  for _ in range(20000):solver.run_iteration()
  node=self.native.NativeState(g)
  for a in [0,5,48,49]:node.apply_action(a)
  before=(solver.iteration,solver.rng_state(),node.audit())
  policy=native_average_policy(self.native,solver);p=policy(node)[0]
  self.assertGreater(p,0)
  result=evaluate_history(node,[0],policy,max_nodes=1)
  self.assertEqual(result['conditional_ev'],[Fraction(-1),Fraction(1)])
  self.assertEqual(result['branch_ev_contribution'],[-p,p])
  self.assertEqual((solver.iteration,solver.rng_state(),node.audit()),before)
  self.assertIsNone(result['native_infoset_ev'])
 def test_known_river_chance_and_conditional_ev_are_separate(self):
  node=self.native.NativeState(NativeGame([4,4]))
  for a in [48,49,0,1,6,1,8,17,26,32]:node.apply_action(a)
  self.assertTrue(node.is_chance_node())
  result=evaluate_history(node,[41],lambda state:{1:Fraction(1)},max_nodes=1)
  self.assertEqual(result['reach']['chance_reach'],Fraction(1,44))
  self.assertEqual(result['conditional_ev'],[Fraction(4),Fraction(-4)])
  self.assertEqual(result['branch_ev_contribution'],[Fraction(1,11),Fraction(-1,11)])
 def test_mutating_policy_is_rejected_without_touching_original_state(self):
  node=self.native.NativeState(NativeGame([4,4]))
  for a in [48,49,0,1]:node.apply_action(a)
  before=node.audit()
  def mutate(state):state.apply_action(0);return {0:Fraction(1)}
  with self.assertRaises(ValueError):trace_history(node,[0],mutate)
  self.assertEqual(node.audit(),before)
if __name__=='__main__':unittest.main()

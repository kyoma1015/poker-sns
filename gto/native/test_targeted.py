"""Experimental full-support proposal and unchanged native-action acceptance."""
import importlib,os,sys,unittest,math
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame
from gto.native.preflop import decision
from gto.native.ordinary_study import context_coverage
class Proposal(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_TARGETED_MODULE_DIR']);cls.n=importlib.import_module('pokerid_targeted')
 def test_full_support_normalization_and_importance_identity(self):
  for actions in ([0,1,7,20,44,102],[0,1,8],[1]):
   for stage in range(4):
    for raises in range(5):
     current=[1/len(actions)]*len(actions);q=self.n.targeted_sampling(current,.6,actions,stage,raises)
     self.assertTrue(all(p>0 for p in q));self.assertAlmostEqual(sum(q),1)
     values=[float(a-30) for a in actions]
     # Full summation of the sampled estimator, including importance weights.
     estimate=sum(q[i]*(current[i]*values[i]/q[i]) for i in range(len(q)))
     self.assertAlmostEqual(estimate,sum(p*v for p,v in zip(current,values)))
 def test_stage_specific_focus_without_action_pruning(self):
  actions=[0,1,7,20,44,102];current=[1/6]*6
  for raises,target in enumerate((7,20,44,1)):
   q=self.n.targeted_sampling(current,.6,actions,0,raises)
   self.assertEqual(actions[q.index(max(q))],target);self.assertGreater(max(q),.5)
  for actual,expected in zip(self.n.targeted_sampling(current,.6,actions,1,0),current):self.assertAlmostEqual(actual,expected)
 def test_invalid_proposals_fail_closed(self):
  for p,e,a,r,b in (([1],0,[1],0,0),([float('nan')],.6,[1],0,0),([1],.6,[1,2],0,0),([.5,.5],.6,[1,1],0,0)):
   with self.assertRaises(RuntimeError):self.n.targeted_sampling(p,e,a,r,b)
 def test_native_game_retains_all_raise_sizes_and_postflop(self):
  game=NativeGame([100,100]);state=decision(self.n,game,[])
  self.assertIn(102,state.legal_actions());self.assertIn(8,state.legal_actions())
  solver=self.n.Solver(game,.6,17,True,True,.1)
  for _ in range(2000):solver.run_iteration()
  root=context_coverage(self.n,solver,game,[])
  facing=context_coverage(self.n,solver,game,[7,20])
  self.assertGreater(facing['updated_orderings'],0)
  self.assertTrue(any(__import__('json').loads(k)['board'] for k in solver.keys()))
  self.assertEqual([x['id'] for x in root['actions']],state.legal_actions())
if __name__=='__main__':unittest.main()

"""Actual separately compiled exact-fold control, not a native-source stub."""
import importlib,os,sys,tempfile,unittest
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.feasible_response import CompletedPolicy,LockedOpponentGame,response_snapshot
from gto.native.infoset_export import PolicySnapshot
from gto.native.training import NativeGame,checkpoint
from gto.native.checkpoints import load_verified_checkpoint

class OneDecision:
 def __init__(self):self.action=None
 def is_terminal(self):return self.action is not None
 def is_chance_node(self):return False
 def current_player(self):return 0
 def information_state_string(self,player):return 'one-decision-exact-fold'
 def legal_actions(self):return [0,1]
 def exact_action_values(self):
  if self.is_terminal():raise AssertionError('exact control captured after state mutation')
  return {0:-1.}
 def apply_action(self,action):self.action=action
 def player_return(self,player):return -1. if self.action==0 else 1.
class Toy:
 def num_players(self):return 1
 def new_initial_state(self):return OneDecision()

class ExactControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_RESPONSE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_response')
 def base(self):return CompletedPolicy(PolicySnapshot({'other':{1:F(1)}}),'uniform_legal_prior')
 def test_actual_estimator_removes_fold_draw_variance_without_bias(self):
  samples=set()
  for seed in range(20):
   solver=self.native.Solver(Toy(),.6,seed,True,True,.1);solver.run_iteration()
   row=solver.row('one-decision-exact-fold');chosen=next(iter(row['samples']));samples.add(chosen)
   expected=[-.5,.5] if chosen==0 else [-1.5,1.5]
   self.assertEqual(row['regret'],expected)
  self.assertEqual(samples,{0,1})
  # Enumeration of both equiprobable draws: same expected regret as ordinary
  # outcome sampling, while its fold estimator would have values(-2,0).
  self.assertEqual([(-.5-1.5)/2,(.5+1.5)/2],[-1,1])
 def test_exact_control_disabled_restores_original_sampling_update(self):
  solver=self.native.Solver(Toy(),.6,701,False,True,.1);solver.run_iteration()
  self.assertEqual(solver.row('one-decision-exact-fold')['regret'],[-1,1])
 def test_public_history_fold_baseline_matches_actual_full_native_terminal(self):
  game=NativeGame([100,100]);locked=LockedOpponentGame(self.native,game,0,self.base(),exact_fold_baseline=True)
  for actions,value in (([],-1),([7,20],-5),
       ([1,1,8,17,26,12],-2),
       ([1,1,8,17,26,1,8,16],-8)):
   node=locked.new_initial_state()
   for action in [48,49,0,1]+actions:node.apply_action(action)
   self.assertEqual(node.exact_action_values(),{0:value})
   node.apply_action(0);self.assertTrue(node.is_terminal());self.assertEqual(node.player_return(0),value)
 def test_full_response_checkpoint_and_rng_resume(self):
  game=LockedOpponentGame(self.native,NativeGame([100,100]),0,self.base(),exact_fold_baseline=True)
  solver=self.native.Solver(game,.6,701,True,True,.1)
  for _ in range(50):solver.run_iteration()
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'anchored.bin';checkpoint(solver,path,'exact-fold-control-test-v1')
   other=self.native.Solver(game,.6,701,True,True,.1);load_verified_checkpoint(other,path,'exact-fold-control-test-v1')
   for _ in range(50):solver.run_iteration();other.run_iteration()
   self.assertEqual(response_snapshot(solver).digest,response_snapshot(other).digest)
   self.assertEqual(solver.rng_state(),other.rng_state())
if __name__=='__main__':unittest.main()

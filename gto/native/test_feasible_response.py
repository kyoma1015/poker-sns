from fractions import Fraction as F
import importlib,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.native.training import NativeGame,checkpoint
from gto.native.checkpoints import load_verified_checkpoint
from gto.native.infoset_export import PolicySnapshot
from gto.native.feasible_response import CompletedPolicy,LockedOpponentGame,LockedState,response_snapshot,evaluate,terminal_trajectory
class FeasibleNative(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_g12')
 def base(self):return CompletedPolicy(PolicySnapshot({'unrelated':{1:F(1)}}),'uniform_legal_prior')
 def deal(self,cards):
  node=self.native.NativeState(NativeGame([100,100]))
  for card in cards:node.apply_action(card)
  return node
 def test_opponent_choices_become_fixed_chance_without_information_leak(self):
  node=self.deal([48,49,0,1]);wrapper=LockedState(node,0,self.base())
  key=wrapper.information_state_string(0);wrapper.apply_action(7)
  self.assertTrue(wrapper.is_chance_node());self.assertAlmostEqual(sum(p for _,p in wrapper.chance_outcomes()),1)
  with self.assertRaises(ValueError):wrapper.information_state_string(0)
  other=self.deal([48,49,4,5]);self.assertEqual(other.information_state_string(0),key)
  self.assertEqual(self.base()(other),self.base()(self.deal([48,49,0,1])))
 def test_actual_single_updater_training_checkpoint_resume_and_frozen_policy(self):
  locked=LockedOpponentGame(self.native,NativeGame([100,100]),0,self.base())
  a=self.native.Solver(locked,.6,701,True,True,.1);b=self.native.Solver(locked,.6,701,True,True,.1)
  for _ in range(100):a.run_iteration()
  for _ in range(50):b.run_iteration()
  with tempfile.TemporaryDirectory() as directory:
   path=Path(directory)/'response.bin';checkpoint(b,path,'locked-response-test-v1')
   c=self.native.Solver(locked,.6,701,True,True,.1);load_verified_checkpoint(c,path,'locked-response-test-v1')
   for _ in range(50):c.run_iteration()
   one=response_snapshot(a);two=response_snapshot(c)
   self.assertEqual(one.digest,two.digest);self.assertFalse(a.stats()['native_engine'])
   a.run_iteration();self.assertEqual(one.digest,two.digest)
 def test_heldout_identical_profiles_have_exact_zero_gain_and_repeat(self):
  game=NativeGame([100,100]);policy=self.base()
  a=evaluate(self.native,game,policy,policy,samples=16,seed=100017)
  b=evaluate(self.native,game,policy,policy,samples=16,seed=100017)
  self.assertEqual(a,b);self.assertEqual(a['global']['gain']['mean_bb'],0)
  self.assertEqual(a['global']['gain']['sum_squared_chips'],0)
  self.assertIsNone(a['original_partial_policy_ev']);self.assertFalse(a['full_game_convergence_verified'])
  self.assertGreater(a['completion_usage'][0]['completed'],0)
 def test_real_postflop_decisions_and_settlement_are_preserved(self):
  game=NativeGame([100,100]);cards=[48,49,0,1,8,17,26,32,35]
  cards+= [c for c in range(52) if c not in cards];node=self.native.NativeState(game);rows={};offset=0
  while not node.is_terminal():
   if node.is_chance_node():node.apply_action(cards[offset]);offset+=1
   else:
    rows[node.information_state_string(node.current_player())]={a:F(int(a==1)) for a in node.legal_actions()}
    node.apply_action(1)
  policy=CompletedPolicy(PolicySnapshot(rows),'uniform_legal_prior')
  values,counts=terminal_trajectory(self.native,game,cards,123,policy)
  self.assertEqual(values,node.settlement()['net']);self.assertEqual(sum(values),0)
  self.assertEqual(counts['postflop_decisions'],6);self.assertEqual(counts['completed'],0)
 def test_wrong_player_or_nonexplicit_completion_is_refused(self):
  with self.assertRaises(ValueError):LockedOpponentGame(self.native,NativeGame([100,100]),2,self.base())
  with self.assertRaises(ValueError):evaluate(self.native,NativeGame([100,100]),self.base(),self.base(),samples=1)
if __name__=='__main__':unittest.main()

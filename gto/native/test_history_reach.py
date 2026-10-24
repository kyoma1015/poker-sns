"""Finite actual-native path reach and policy EV; not infoset-equilibrium proof."""
from fractions import Fraction
import importlib,json,math,os
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from gto.native.history_reach import trace_history,evaluate_history,native_average_policy
from gto.native.training import NativeGame,train_batch

class HistoryReach(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  sys.path.insert(0,os.environ['GTO_NATIVE_MODULE_DIR']);cls.native=importlib.import_module('pokerid_g12')
 def game(self,n=2):return NativeGame([4]*n)
 def state(self,n=2):
  s=self.native.NativeState(self.game(n))
  for a in [48,49,0,1] if n==2 else range(2*n):s.apply_action(a)
  return s
 def mixed(self,node):
  # Free checks cannot fold. Put residual mass on an actually legal non-call action.
  other=next(a for a in node.legal_actions() if a!=1)
  return {other:Fraction(2,3),1:Fraction(1,3)} if node.current_player()==0 else {other:Fraction(1,2),1:Fraction(1,2)}
 def test_full_deal_path_reach_is_not_own_hand_marginal(self):
  s=self.native.NativeState(self.game());before=s.audit()
  r=trace_history(s,[48,49,0,1],self.mixed)
  self.assertEqual(r['chance_reach'],Fraction(1,math.perm(52,4)))
  self.assertNotEqual(r['chance_reach'],Fraction(1,2652))
  self.assertEqual(r['strategy_reach'],[Fraction(1),Fraction(1)])
  self.assertEqual(s.audit(),before)
 def test_nonempty_action_history_separates_each_player_strategy(self):
  r=trace_history(self.state(),[1,1],self.mixed)
  self.assertEqual(r['chance_reach'],1);self.assertEqual(r['strategy_reach'],[Fraction(1,3),Fraction(1,2)])
  self.assertEqual(r['joint_reach'],Fraction(1,6));self.assertEqual(len(r['state'].audit()['history']),2)
 def test_flop_chance_and_strategy_compose(self):
  r=trace_history(self.state(),[1,1,8,17,26],self.mixed)
  self.assertEqual(r['chance_reach'],Fraction(1,48*47*46))
  self.assertEqual(r['joint_reach'],Fraction(1,6*48*47*46))
  self.assertEqual(r['state'].audit()['board'],[8,17,26])
 def test_fold_conditional_ev_and_unconditional_branch_contribution(self):
  r=evaluate_history(self.state(),[0],self.mixed)
  self.assertEqual(r['conditional_ev'],[Fraction(-1),Fraction(1)])
  self.assertEqual(r['branch_ev_contribution'],[Fraction(-2,3),Fraction(2,3)])
  self.assertIsNone(r['native_infoset_ev'])
 def test_real_river_policy_ev(self):
  s=self.state()
  for a in [1,1,8,17,26,1,1,32,1,1,41]:s.apply_action(a)
  r=evaluate_history(s,[],lambda node:{1:Fraction(1)},max_nodes=10)
  self.assertEqual(r['conditional_ev'],[Fraction(2),Fraction(-2)])
  self.assertEqual(r['reach']['joint_reach'],1)
 def test_zero_reach_does_not_invent_conditional_ev(self):
  r=evaluate_history(self.state(),[0],lambda node:{1:Fraction(1)},max_nodes=1)
  self.assertIsNone(r['conditional_ev']);self.assertIsNone(r['branch_ev_contribution'])
  self.assertEqual(r['reach']['joint_reach'],0)
 def test_first_actor_reach_for_all_player_counts(self):
  for n in range(2,10):
   s=self.state(n);actor=s.current_player();r=trace_history(s,[0],lambda node:{0:Fraction(1,4),1:Fraction(3,4)})
   self.assertEqual(r['strategy_reach'],[Fraction(1,4) if p==actor else Fraction(1) for p in range(n)])
 def test_step_bound_illegal_action_and_trailing_terminal_refuse(self):
  for actions,kwargs in [([1,1],{'max_steps':1}),([99],{}),([True],{}),([0,1],{})]:
   with self.subTest(actions=actions),self.assertRaises(ValueError):trace_history(self.state(),actions,self.mixed,**kwargs)
 def test_invalid_or_inexact_strategy_probabilities_refuse(self):
  for policy in [{0:.5,1:.5},{0:Fraction(1,3)},{0:Fraction(-1),1:Fraction(2)},{999:Fraction(1)}]:
   with self.subTest(policy=policy),self.assertRaises(ValueError):trace_history(self.state(),[0],lambda node:policy)
 def test_actual_native_average_policy_is_exact_and_readonly(self):
  g=self.game();s=self.native.Solver(g,.6,17,True,True,.1)
  for _ in range(20000):s.run_iteration()
  node=self.state();before=(s.iteration,s.rng_state());policy=native_average_policy(self.native,s);p=policy(node)
  self.assertEqual(sum(p.values()),1);self.assertTrue(all(isinstance(x,Fraction) for x in p.values()))
  self.assertEqual(set(p),set(node.legal_actions()));self.assertEqual((s.iteration,s.rng_state()),before)
  r=trace_history(node,[0],policy);self.assertEqual(r['joint_reach'],p[0])
 def test_missing_or_changed_native_average_policy_refuses(self):
  g=self.game();s=self.native.Solver(g,.6,17,True,True,.1);policy=native_average_policy(self.native,s)
  with self.assertRaises(ValueError):policy(self.state())
  s.run_iteration()
  with self.assertRaises(ValueError):policy(self.state())
 def test_checkpoint_resume_preserves_strategy_reach(self):
  g=self.game();a=self.native.Solver(g,.6,17,True,True,.1);b=self.native.Solver(g,.6,17,True,True,.1)
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);train_batch(a,g,4000,p/'all');train_batch(b,g,2000,p/'first')
   c=self.native.Solver(g,.6,17,True,True,.1);train_batch(c,g,2000,p/'second',resume=p/'first')
   self.assertEqual(a.rng_state(),c.rng_state())
   x=trace_history(self.state(),[0],native_average_policy(self.native,a));y=trace_history(self.state(),[0],native_average_policy(self.native,c))
   self.assertEqual(x['joint_reach'],y['joint_reach']);self.assertEqual(x['strategy_reach'],y['strategy_reach'])

if __name__=='__main__':unittest.main()

from fractions import Fraction as F
import unittest
from gto.native.feasible_response import CompletedPolicy,moments_interval
from gto.native.infoset_export import PolicySnapshot,UnknownPolicyRow
class ObservationOnly:
 def is_terminal(self):return False
 def is_chance_node(self):return False
 def current_player(self):return 0
 def information_state_string(self,player):return 'hero_public_information'
 def legal_actions(self):return [0,1]
 def audit(self):raise AssertionError('private/world audit leaked into policy')
class Feasible(unittest.TestCase):
 def test_completion_requires_explicit_declaration_and_keeps_strict_snapshot_strict(self):
  strict=PolicySnapshot({'other':{1:F(1)}});node=ObservationOnly()
  with self.assertRaises(UnknownPolicyRow):strict(node)
  completed=CompletedPolicy(strict,'uniform_legal_prior')
  self.assertEqual(completed.decide(node),({0:F(1,2),1:F(1,2)},True))
  with self.assertRaises(ValueError):CompletedPolicy(strict,'automatic')
  with self.assertRaises(UnknownPolicyRow):strict(node)
 def test_observed_policy_uses_no_world_audit(self):
  strict=PolicySnapshot({'hero_public_information':{0:F(1,4),1:F(3,4)}})
  completed=CompletedPolicy(strict,'uniform_legal_prior')
  self.assertEqual(completed.decide(ObservationOnly()),({0:F(1,4),1:F(3,4)},False))
 def test_intervals_are_finite_bounded_and_inconclusive_at_small_counts(self):
  self.assertEqual(moments_interval(0,0,0,-1,1,.01)['mean'],None)
  one=moments_interval(1,1,1,-1,1,.01)
  self.assertLessEqual(one['interval'][0],0)
  large=moments_interval(10000,10000,10000,-1,1,.01)
  self.assertLess(large['interval'][1]-large['interval'][0],one['interval'][1]-one['interval'][0])
 def test_impossible_moments_and_bad_controls_refused(self):
  for args in ((10,0,10,-1,1,.01),(0,-1,2,-1,1,.01),(0,0,True,-1,1,.01),(1,0,0,-1,1,.01),(0,float('nan'),2,-1,1,.01)):
   with self.assertRaises(ValueError):moments_interval(*args)
if __name__=='__main__':unittest.main()

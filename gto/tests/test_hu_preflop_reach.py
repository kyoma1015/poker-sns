from fractions import Fraction as F
import unittest
from gto.native.hu_preflop_reach import PAIRS,blocker_sums
class Blockers(unittest.TestCase):
 def test_uniform_full_deck_preserves2450ordered_opponent_assignments(self):
  compatible,d=blocker_sums(dict.fromkeys(PAIRS,F(1)))
  self.assertEqual(d,1);self.assertEqual(set(compatible.values()),{2450})
 def test_blocker_identity_matches_full_enumeration_for_nonuniform_factors(self):
  weights={p:F(((p[0]*7+p[1]*3)%19),23) for p in PAIRS}
  compatible,d=blocker_sums(weights)
  for hero in ((0,1),(0,51),(25,26),(50,51)):
   expected=sum((v for p,v in weights.items() if not set(p)&set(hero)),F(0))
   self.assertEqual(F(compatible[hero],d),expected)
 def test_missing_negative_and_unnormalizable_factors_rejected(self):
  full=dict.fromkeys(PAIRS,F(1));short=full.copy();short.pop((0,1))
  negative=full.copy();negative[0,1]=F(-1)
  for bad in (short,negative,dict.fromkeys(PAIRS,1.0)):
   with self.assertRaises(ValueError):blocker_sums(bad)
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from gto.qualification import range_ev
class ConditionalEV(unittest.TestCase):
 def test_exact_fixed_board_card_removal_ties_and_weighted_expectation(self):
  # Royal on board: every legal pair ties identically; no sampling fluctuation.
  board=[32,36,40,44,48];pairs=[[5,6],[9,10]];x,tv=range_ev.equity([0,1],pairs,[.3,.7],4096,17,board);self.assertEqual(x,.5);self.assertLess(tv,1e-12)
  with self.assertRaisesRegex(ValueError,'conditional range'):range_ev.equity([0,1],[[0,5]],[1.],2,1,board)
 def test_bounded_variance_envelope_and_spending(self):
  for x in ([0.,.5,1.],[.1,.1,.9,.9],[.5]*8):
   n=len(x);self.assertLessEqual(np.var(x,ddof=1),n*np.mean(x)*(1-np.mean(x))/(n-1)+1e-15)
  self.assertLess(sum(1/(k*(k+1)) for k in range(1,10000)),1)
  self.assertLess(range_ev.radius(.9,1000000,1e-7),range_ev.radius(.5,1000000,1e-7))
 def test_zero_call_exact_profit(self):
  x=range_ev.cell([0,1],[[5,6]],[1.],[0.],4.,delta=1e-6,seed=1);self.assertTrue(x['exact']);self.assertEqual(x['interval'],[4.,4.])
 def test_weighted_nontrivial_fixed_board_expectation(self):
  # HeroAA makes wheel; KK loses,66 makes six-high straight and wins.
  x,_=range_ev.equity([48,49],[[44,45],[16,17]],[.25,.75],200000,17162101,[0,5,10,15,20]);self.assertAlmostEqual(x,.25,delta=.01)

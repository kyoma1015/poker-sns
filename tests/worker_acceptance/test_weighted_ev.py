"""Decimal oracle for finite reach-weighted EV scaling (not strategy evidence)."""
from decimal import Decimal,localcontext
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.hand169 import aggregate
class WeightedEV(unittest.TestCase):
 def check(self,weights,evs):
  rows=[{'cards':cards,'weight':w,'frequencies':[1.0],'ev':e} for cards,w,e in zip((['As','Ks'],['Ah','Kh']),weights,evs)]
  with localcontext() as c:
   c.prec=1500
   exact=float(sum((Decimal.from_float(w)*Decimal.from_float(e) for w,e in zip(weights,evs)),Decimal(0))/sum((Decimal.from_float(w) for w in weights),Decimal(0)))
  result=aggregate(rows,1,require_complete=False)['hands']['AKs']['ev']
  self.assertAlmostEqual(result/exact,1.0,places=14) if exact else self.assertEqual(result,0.0)
 def test_positive_representable_contribution(self):self.check([1e308,1e-16],[0.0,1e308])
 def test_negative_representable_contribution(self):self.check([1e308,1e-16],[0.0,-1e308])
 def test_small_weight_product_before_normalization(self):self.check([1e-300,1e-300],[1e-100,2e-100])
 def test_large_product_no_overflow(self):self.check([1e308,1e307],[1e308,-1e308])
 def test_zero_ev_and_zero_weight(self):self.check([1e308,0.0],[0.0,1e308])

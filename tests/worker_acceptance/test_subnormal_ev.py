"""Independent exact oracle at subnormal term rounding boundaries."""
from decimal import Decimal,localcontext
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.hand169 import aggregate
class SubnormalEV(unittest.TestCase):
 def check(self,value):
  rows=[{'cards':cards,'weight':w,'ev':e,'frequencies':[1.0]} for cards,w,e in [(['As','Ks'],1.0,0.0),(['Ah','Kh'],5e-324,value),(['Ad','Kd'],5e-324,value),(['Ac','Kc'],5e-324,value)]]
  # Preserve the existing exported float mass denominator; only term rounding changes.
  with localcontext() as c:
   c.prec=1500
   expected=float(sum((Decimal.from_float(r['weight'])*Decimal.from_float(r['ev']) for r in rows),Decimal(0))/Decimal.from_float(math.fsum(r['weight'] for r in rows)))
  result=aggregate(rows,1,require_complete=False)['hands']['AKs']
  self.assertEqual(result['ev'],expected)
  self.assertEqual(result['reach_mass'],1.0)
 def test_positive_terms_round_up_only_after_sum(self):self.check(.4)
 def test_negative_terms_round_up_only_after_sum(self):self.check(-.4)
 def test_positive_terms_not_individually_overrounded(self):self.check(.6)
 def test_negative_terms_not_individually_overrounded(self):self.check(-.6)

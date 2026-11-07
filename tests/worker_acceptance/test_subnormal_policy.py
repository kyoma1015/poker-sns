from decimal import Decimal,localcontext
import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from gto.hand169 import aggregate
class SubnormalPolicy(unittest.TestCase):
 def check(self,frequency,count):
  rows=[{'cards':['As','Ks'],'weight':1e308,'frequencies':[1.,0.],'ev':0.}]
  rows.extend({'cards':cards,'weight':5e-16,'frequencies':[1-frequency,frequency],'ev':0.} for cards in (['Ah','Kh'],['Ad','Kd'],['Ac','Kc'])[:count])
  with localcontext() as c:
   c.prec=1500;expected=[float(sum((Decimal.from_float(r['weight'])*Decimal.from_float(r['frequencies'][a]) for r in rows),Decimal(0))/Decimal.from_float(math.fsum(r['weight'] for r in rows))) for a in range(2)]
  result=aggregate(rows,2,require_complete=False)['hands']['AKs'];self.assertEqual(result['frequencies'],expected);self.assertEqual(result['ev'],0.)
 def test_three_small_terms(self):self.check(.4,3)
 def test_two_small_terms(self):self.check(.4,2)
 def test_three_overrounded_terms(self):self.check(.6,3)
 def test_two_overrounded_terms(self):self.check(.6,2)

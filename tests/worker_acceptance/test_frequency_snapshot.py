import math
import unittest
from gto.hand169 import aggregate
class FrequencySnapshot(unittest.TestCase):
 def test_stream_reused_buffer_preserves_each_validated_row(self):
  buffer=[1.,0.]
  def records():
   yield {'cards':['As','Ks'],'weight':1.,'frequencies':buffer,'ev':2.}
   buffer[:]=[0.,1.]
   yield {'cards':['Ah','Kh'],'weight':3.,'frequencies':buffer,'ev':6.}
  out=aggregate(records(),2,require_complete=False)['hands']['AKs']
  self.assertEqual(out['frequencies'],[.25,.75]);self.assertEqual(out['reach_mass'],4.);self.assertEqual(out['ev'],5.)
  self.assertEqual(buffer,[0.,1.])
 def test_post_yield_mutation_cannot_introduce_unvalidated_nan(self):
  buffer=[1.,0.]
  def records():
   yield {'cards':['As','Ks'],'weight':1.,'frequencies':buffer,'ev':None}
   buffer[:]=[float('nan'),1.]
  out=aggregate(records(),2,require_complete=False)['hands']['AKs']
  self.assertEqual(out['frequencies'],[1.,0.]);self.assertTrue(all(map(math.isfinite,out['frequencies'])))
  self.assertTrue(math.isnan(buffer[0]));self.assertIsNone(out['ev'])
 def test_tuple_list_and_zero_mass_stay_supported(self):
  out=aggregate([{'cards':['As','Ks'],'weight':0,'frequencies':(0.,1.),'ev':None}],2,require_complete=False)['hands']['AKs']
  self.assertIsNone(out['frequencies']);self.assertIsNone(out['ev'])

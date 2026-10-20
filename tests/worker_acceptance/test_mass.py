import unittest
from gto.hand169 import aggregate

class WorkerMassAcceptance(unittest.TestCase):
    def test_finite_sum_overflow_is_validation_error(self):
        rows=[{'cards':['As','Ks'],'weight':1e308,'frequencies':[1.0],'ev':0.0},
              {'cards':['Ah','Kh'],'weight':1e308,'frequencies':[1.0],'ev':0.0}]
        with self.assertRaises(ValueError):
            aggregate(rows,1,require_complete=False)

    def test_normal_weighted_output_is_preserved(self):
        rows=[{'cards':['As','Ks'],'weight':1.,'frequencies':[1.,0.],'ev':1.},
              {'cards':['Ah','Kh'],'weight':3.,'frequencies':[0.,1.],'ev':3.}]
        result=aggregate(rows,2,require_complete=False)['hands']['AKs']
        self.assertEqual(result['frequencies'],[.25,.75])
        self.assertEqual(result['ev'],2.5)

import os,copy,unittest
from gto.qualification import native_tree_bound as bound,stream_chance as sc
from gto.qualification.build import load
@unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
class NativeBound(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.rules,_=load(os.environ['QUALIFICATION_BUILD'])
 def test_complete_HU1BB_actions_exact_terminal_basis_not_fullchance_certificate(self):
  nodes=[dict(actor=0,round=0,native_actions=[0,1],children=[1,2]),dict(actor=-1,c0=-.5,c1=0,children=[]),dict(actor=-1,c0=-1,c1=2,children=[])]
  x=bound.verify(nodes,self.rules,(2,2));self.assertTrue(x['complete_action_coverage']);self.assertTrue(x['covered_terminal_basis_exact']);self.assertIsNone(x['full_native_NashConv_upper'])
  wrong=copy.deepcopy(nodes);wrong[2]['c1']=2.1;y=bound.verify(wrong,self.rules,(2,2));self.assertFalse(y['covered_terminal_basis_exact']);self.assertGreater(y['max_terminal_basis_error'],0)
 def test_HU50_all_covered_terminal_rewards_but_omitted_sizes_UNKNOWN(self):
  ns=sc.expanded_tree(self.rules,[0,1,6,7,8,9,10,12,16,18,19,102],[23]);x=bound.verify(ns,self.rules);self.assertTrue(x['covered_terminal_basis_exact']);self.assertEqual(len(x['omitted'][0]['omitted']),87);self.assertIsNone(x['omitted_size_error_upper']);self.assertIsNone(x['full_native_NashConv_upper'])

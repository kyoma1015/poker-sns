import os,tempfile,unittest
import numpy as np
from gto.qualification import adaptive_support as support,active_chance as ac,stream_sampling as ss,public_chance_solver as pcs,stream_measure
from gto.qualification.build import load
class NativeSupport(unittest.TestCase):
 @unittest.skipUnless(os.environ.get('QUALIFICATION_BUILD'),'native build required')
 def test_generic_root_size_budget_and_joint_response_update(self):
  rules,_=load(os.environ['QUALIFICATION_BUILD']);root=[0,1,6,7,8,9,10,12,16,18,19,102]
  nodes,receipt=support.expand(rules,root,[dict(action=11,CF_residual=.3),dict(action=21,CF_residual=.2),dict(action=999,CF_residual=100)],max_new=1)
  self.assertEqual(receipt['accepted'],[11]);self.assertEqual(len(receipt['support']),13);self.assertEqual(receipt['omitted'],86);self.assertIsNone(receipt['omitted_size_error_upper'])
  self.assertTrue(any(n['actor']>=0 and n['native_prefix'] and n['native_prefix'][0][2]==9 for n in nodes)) #4.5BB=9chips
  with tempfile.TemporaryDirectory() as tmp:
   lib=ac.build(tmp);q=ss.Game(lib,nodes,[dict(pcs.block(lib,[0,5,10,15,20],1.),stratum=(0,False,True))]);q.step();rootat=q.base[0];self.assertTrue(np.any(q.A[rootat:rootat+169*13]>0));self.assertTrue(np.any(q.visits>0));m=stream_measure.measure(q);self.assertGreaterEqual(m['NashConv_bb'],0)
  _,small=support.expand(rules,root,[dict(action=11,CF_residual=.3)],max_nodes=3923);self.assertEqual(small['accepted'],[]);self.assertEqual(small['budget_rejected'],[11])

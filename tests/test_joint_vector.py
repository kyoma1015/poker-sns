import tempfile,unittest
from pathlib import Path
from gto.abstract import joint_stream as s,joint_vector as v,joint_update_audit as audit
class VectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.tmp=tempfile.TemporaryDirectory();cls.old=s.build(Path(cls.tmp.name)/'old');cls.new=v.build(Path(cls.tmp.name)/'new')
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def test_tiny_explicit_path_gradients_average_and_enumerated_BR(self):
        results=[]
        for b,pi in enumerate(audit.policies()):
            old=audit.native(self.old,b,pi);new=audit.native(self.new,b,pi)
            for field in old:
                if field=='ev':self.assertAlmostEqual(old[field],new[field],delta=1e-12)
                else:
                    for x,y in zip(old[field],new[field]):self.assertAlmostEqual(x,y,delta=1e-12, msg=field)
            results.append(new)
        for owner,z in enumerate(audit.native_br(results)):self.assertAlmostEqual(z,audit.brute_br(audit.policies(),owner),delta=1e-12)
    def test_actual_public_tree_all_outputs_for_nonuniform_profiles(self):
        ns,base,rows,P,S,b=s.layout(2);obj={'codes':[0,8]};values=[.2,.02,.3,.12,.1,.07,.4,.36]
        for phase in range(3):
            reg=[float((i*7+phase)%11-5) for i in range(S)];avg=[float((i*3+phase)%7) for i in range(S)]
            for averaged in (False,True):
                old=s.block(self.old,obj,values,reg,avg,averaged);new=s.block(self.new,obj,values,reg,avg,averaged)
                for field in ('grad','avg','leaf','metrics','action_num','action_den'):
                    for x,y in zip(old[field],new[field]):self.assertAlmostEqual(x,y,delta=1e-10,msg=field)
    def test_non_normalized_policy_is_rejected(self):
        pi=audit.policies()[0];pi[:2]=[.8,.8]
        with self.assertRaises(ValueError):audit.native(self.new,0,pi)
    def test_zero_own_reach_does_not_remove_counterfactual_regret(self):
        pi=audit.policies()[0];pi[:2]=[1.,0.];out=audit.native(self.new,0,pi);self.assertEqual(out['avg'][8:10],[0.,0.]);self.assertGreater(max(abs(x) for x in out['grad'][8:10]),.01)
if __name__=='__main__':unittest.main()

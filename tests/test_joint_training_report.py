import copy,unittest
from gto.abstract.joint_training_report import compare

class ReportTests(unittest.TestCase):
    def setUp(self):
        self.point={'complete_epoch':True,'blocks':3510,'parent_logical_digest':'actual','cpu_seconds':10.}
        self.parity={'orbits':1755,'max_array_difference':1e-12,'max_policy_difference':1e-12}
        self.evaluation={'coverage':1,'evaluated_orbits':1755,'epoch':4,'restricted_nashconv_interval_bb':[1.,1.],'sb_br_gain_bb':.4,'bb_br_gain_bb':.6}
    def call(self):return compare(self.point,copy.deepcopy(self.point),self.parity,{k:self.evaluation for k in ('legacy','vector')})
    def test_partial_or_changed_history_cannot_claim_speedup(self):
        self.point['complete_epoch']=False
        with self.assertRaises(ValueError):self.call()
        self.point['complete_epoch']=True;other={**self.point,'parent_logical_digest':'invented'}
        with self.assertRaisesRegex(ValueError,'history'):compare(self.point,other,self.parity,{})
    def test_sampling_or_incomplete_br_is_not_complete_evidence(self):
        self.evaluation['coverage']=.99
        with self.assertRaisesRegex(ValueError,'independent BR'):self.call()
    def test_tolerance_failure_is_explicit_never_gto_promotion(self):
        self.parity['max_policy_difference']=.1;r=self.call();self.assertFalse(r['policy_parity_pass']);self.assertEqual(r['normal_GTO_added'],0);self.assertEqual(r['formal_acceptance'],[0,12])
if __name__=='__main__':unittest.main()

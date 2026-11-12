import copy,json,unittest
from pathlib import Path
from gto.native.replay_reference import verify

class ReplayReference(unittest.TestCase):
    def setUp(self):
        self.reference=json.loads(Path('docs/qa/strict-continuation-20261030/evidence-cb46da.json').read_text())
    def test_observed_ci_reference_preserves_research_scope(self):
        result=verify(self.reference,self.reference)
        self.assertTrue(result['independent_build_replay_verified'])
        self.assertEqual(result['new_statistical_sample_sets'],0)
        self.assertFalse(result['ordinary_gto_certificate'])
    def test_changed_policy_trace_ev_coverage_or_certificate_is_rejected(self):
        cases=[]
        for field in ('parent_sha256','checkpoint_sha256'):
            x=copy.deepcopy(self.reference);x[field]='0'*64;cases.append(x)
        x=copy.deepcopy(self.reference);x['strict_evaluation']['trajectory_sha256']='0'*64;cases.append(x)
        x=copy.deepcopy(self.reference);x['strict_evaluation']['global']['raw_endpoint_moments'][0][0]+=1;cases.append(x)
        x=copy.deepcopy(self.reference);x['contexts'][3]['complete_frequency_classes']=165;cases.append(x)
        x=copy.deepcopy(self.reference);x['formal_acceptance_complete']=1;cases.append(x)
        for report in cases:
            with self.assertRaises(ValueError):verify(report,self.reference)
        with self.assertRaises(ValueError):verify(cases[-1],cases[-1])
if __name__=='__main__':unittest.main()

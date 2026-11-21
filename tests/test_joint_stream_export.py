import copy,json,unittest
from pathlib import Path
from gto.abstract.joint_stream_export import export

class StreamExportTests(unittest.TestCase):
    def fixture(self):
        p=Path('docs/qa/joint-stream-20261108/results.json')
        if not p.exists():self.skipTest('local full population experiment not published yet')
        r=json.loads(p.read_text());return r['evaluations']['epoch4']
    def test_complete_real_population_rows_and_raise_units(self):
        r=export(self.fixture());self.assertEqual(sum(len(x['hands']) for x in r['ranges']),676)
        self.assertEqual([x['position'] for x in r['ranges']],['SB','BB','SB','BB'])
        self.assertEqual([x['actions'][-1]['raise_to_bb'] for x in r['ranges']],[2.5,9.,21.,50.])
        for x,fold in zip(r['ranges'],[-.5,-1.,-2.5,-9.]):
            for hand in x['hands']:self.assertAlmostEqual(hand['action_ev_bb'][0],fold,delta=1e-8)
    def test_cannot_promote_even_if_restricted_nashconv_zero(self):
        r=copy.deepcopy(self.fixture());r['restricted_nashconv_interval_bb']=[0.,0.]
        with self.assertRaisesRegex(ValueError,'research only'):export(r,normal=True)
        self.assertFalse(export(r)['normal_gto_eligible'])
    def test_missing_ev_and_partial_coverage_fail_closed(self):
        r=copy.deepcopy(self.fixture());r['coverage']=.99
        with self.assertRaisesRegex(ValueError,'population'):export(r)
        r=copy.deepcopy(self.fixture());r['preflop_action_ev_bb'][0]=None
        with self.assertRaisesRegex(ValueError,'missing'):export(r)

if __name__=='__main__':unittest.main()

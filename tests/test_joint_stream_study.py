import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from gto.abstract import joint_stream as s,joint_stream_study as study

class StudyResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);self.rows=[{'representative':[0,4,8],'multiplicity':1}]
    def test_zero_budget_does_not_initialize_or_mark_baseline_ready(self):
        store=s.Store(self.root/'base.sqlite',self.rows);before=store.digest()
        self.assertFalse(study.frozen(store,'unused',seconds=0));self.assertEqual(before,store.digest());self.assertIsNone(store.get('baseline:ready'))
    def test_partial_baseline_file_is_resumed_instead_of_skipped(self):
        baseline=s.Store(self.root/'frozen.sqlite',self.rows)
        with baseline.db:baseline.put('baseline:ready',b'1')
        (self.root/'frozen-evaluation.json').write_text(json.dumps({'coverage':.5}))
        complete={'coverage':1.,'evaluated_orbits':1,'restricted_nashconv_interval_bb':[1.,1.]}
        with patch.object(study.c,'population',return_value=self.rows),patch.object(study.s,'build',return_value=None),patch.object(study.s,'evaluate',return_value=complete) as evaluate,patch.object(study.s.Store,'train',return_value={'blocks':0}):
            result=study.run_locked(self.root,'unused',seconds=30)
        self.assertEqual(evaluate.call_count,1);self.assertEqual(json.loads((self.root/'frozen-evaluation.json').read_text())['coverage'],1.)
        self.assertEqual(result['status'],'BUDGET_OR_CACHE')

if __name__=='__main__':unittest.main()

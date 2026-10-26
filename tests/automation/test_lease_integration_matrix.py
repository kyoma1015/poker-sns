"""Independent source-pinned takeover comparison and actual 8-process WAL QA."""
from pathlib import Path
import concurrent.futures
import importlib.util
import json
import multiprocessing
import os
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import code_worker as w

def task(ident='original',lane='A'):
    return {'id':ident,'lane':lane,'base_sha':'a'*40,'branch':'codex/'+ident,'instruction':'matrix',
            'allowed_paths':['value.py'],'protected_tests':['test.py'],'test_profile':'python'}

def child_claim_activate(path,index):
    leases=w.Leases(path)
    try:
        t=task('parallel-'+str(index),'ABCD'[index%4]);token=leases.claim(t,now=100)
        if token is None:return False
        leases.activate(t['id'],token,{'task':t},now=101)
        return True
    finally:leases.close()

class LeaseIntegration(unittest.TestCase):
    def test_independent_exact_source_comparison_32_pairs(self):
        states=[None,'{','null','true','12','"running"','[]','{}',
          '{"lease_evidence_version":1}',
          '{"worker_liveness":"stopped"}',
          '{"lease_evidence_version":1,"worker_liveness":"unrecognized"}',
          '{"lease_evidence_version":1,"worker_liveness":null}',
          '{"lease_evidence_version":1,"worker_liveness":"stopped","worker_liveness_unknown":"false"}',
          '{"lease_evidence_version":1,"worker_liveness":"unknown","worker_liveness":"stopped"}',
          '{"lease_evidence_version":1,"worker_liveness":"stopped","other":NaN}',
          '{"lease_evidence_version":1,"worker_liveness":"stopped","other":1e999}']
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'original.py'
            source.write_bytes(subprocess.check_output(['git','show','c373286fbe402144148d7862465c2c0ba49d1bea:scripts/code_worker.py'],cwd=ROOT))
            spec=importlib.util.spec_from_file_location('original_matrix_worker',source)
            original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
            counts={};report=[]
            for name,module in [('original',original),('current',w)]:
                successes=0
                for i,evidence in enumerate(states):
                    for lane in 'AB':
                        leases=module.Leases(root/(name+str(i)+lane+'.sqlite'))
                        try:
                            leases.claim(task(),seconds=30,now=100)
                            leases.db.execute("update development_jobs set evidence=? where id='original'",(evidence,))
                            before=leases.db.execute('select * from development_jobs order by id').fetchall()
                            claimed=leases.claim(task('other',lane),now=200) is not None
                            after=leases.db.execute('select * from development_jobs order by id').fetchall()
                            successes+=claimed
                            if name=='current':self.assertTrue(after==before,'current row changed')
                            report.append({'source':name,'case':i,'lane':lane,'claim_succeeded':claimed,'rows_preserved':before==after})
                        finally:leases.close()
                counts[name]=successes
            self.assertEqual(counts,{'original':32,'current':0})
            if os.environ.get('ISSUE22_MATRIX_REPORT'):
                Path(os.environ['ISSUE22_MATRIX_REPORT']).write_text(json.dumps(report,indent=2)+'\n')
            print('Independent comparison: original32/32 unsafe; current0/32; all32 rows retained')
    def test_eight_process_wal_claim_activation_has_one_owner_per_lane(self):
        with tempfile.TemporaryDirectory() as directory:
            state=Path(directory)/'state.sqlite'
            with concurrent.futures.ProcessPoolExecutor(max_workers=8,mp_context=multiprocessing.get_context('spawn')) as pool:
                values=list(pool.map(child_claim_activate,[state]*8,range(8)))
            self.assertEqual(sum(values),4)
            leases=w.Leases(state)
            try:
                self.assertEqual(leases.db.execute('pragma integrity_check').fetchone()[0],'ok')
                self.assertEqual(leases.db.execute('pragma journal_mode').fetchone()[0],'wal')
                self.assertEqual(leases.db.execute("select lane,count(*) from development_jobs where status='running' group by lane order by lane").fetchall(),[(x,1) for x in 'ABCD'])
                for raw,hashed in leases.db.execute('select evidence,spec_hash from development_jobs'):
                    self.assertEqual(json.loads(raw)['claimed_spec_hash'],hashed)
            finally:leases.close()

if __name__=='__main__':unittest.main()

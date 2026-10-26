"""Real multiprocess activation CAS and resume corruption; never held state."""
from pathlib import Path
import concurrent.futures
import json
import multiprocessing
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as w
import test_continuation_recovery as fixture


def activate_child(state,token):
    leases=w.Leases(state)
    try:
        try:leases.activate('next-a',token,{},now=101);return True
        except w.LeaseActivationRefused:return False
    finally:leases.close()

class ActivationCAS(unittest.TestCase):
    def setUp(self):self.f=fixture.RecoveryAcceptance();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def test_many_processes_only_one_activation_wins(self):
        token=self.f.store.leases.claim(self.f.task(),now=100)
        with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
            values=list(pool.map(activate_child,[self.f.state]*8,[token]*8))
        self.assertEqual(sum(values),1)
        raw=self.f.store.db.execute("select evidence from development_jobs where id='next-a'").fetchone()[0]
        self.assertEqual(w.running_evidence_state(raw),'running')
        self.assertEqual(self.f.store.db.execute('pragma integrity_check').fetchone()[0],'ok')
    def test_resume_cas_cannot_overwrite_corrupted_reclaimed_context(self):
        q=w.prepare_host_session(self.f.repo,self.f.work,self.f.state,self.f.task(),now=100)
        self.f.store.defer_host('next-a',q['lease_token'],'transient',agent_stopped=True,now=101,retry_after=1)
        failure=self.f.store.db.execute("select * from continuation_failures where id='next-a'").fetchone()
        original=self.f.store.leases.activate
        def corrupt(*args,**kwargs):
            self.f.store.db.execute("update development_jobs set evidence=NULL where id='next-a'")
            return original(*args,**kwargs)
        with patch.object(self.f.store.leases,'activate',side_effect=corrupt):
            with self.assertRaises(w.LeaseActivationRefused):self.f.store.resume_host('next-a',now=103)
        status,raw=self.f.store.db.execute("select status,evidence from development_jobs where id='next-a'").fetchone()
        self.assertEqual(status,'running');self.assertIsNone(raw)
        self.assertEqual(self.f.store.db.execute("select * from continuation_failures where id='next-a'").fetchone(),failure)
        self.assertTrue(self.f.store.leases.claim(self.f.task('next-b','B'),now=10000) is None)
        self.assertTrue(Path(q['worktree']).is_dir())

if __name__=='__main__':unittest.main()

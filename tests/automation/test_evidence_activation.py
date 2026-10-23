"""No expired/replaced owner may cross a dispatch boundary (temporary real APIs)."""
from pathlib import Path
import json
import sys
import time
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as w
import test_continuation_recovery as fixture

class EvidenceActivation(unittest.TestCase):
    def setUp(self):self.f=fixture.RecoveryAcceptance();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def steal(self,now):
        self.f.store.db.execute("update development_jobs set expires=0 where id='next-a'")
        self.assertTrue(self.f.store.leases.claim(self.f.task('other','B'),now=now) is not None)
    def test_expired_preparation_never_dispatches_executor(self):
        original=w.protected_hashes;once=[];called=[]
        def hashes(*args):
            value=original(*args)
            if not once:once.append(True);self.steal(time.time())
            return value
        with patch.object(w,'protected_hashes',side_effect=hashes):
            r=w.run_task(self.f.repo,self.f.work,self.f.state,self.f.task(),lambda *args:called.append(True))
        self.assertEqual(called,[],'old owner dispatched after expiry/replacement')
        self.assertEqual(r['status'],'blocked')
        self.assertTrue((self.f.work/'next-a').exists())
    def test_expired_host_preparation_never_returns_prepared_token(self):
        original=w.protected_hashes
        def hashes(*args):
            value=original(*args);self.steal(10000);return value
        with patch.object(w,'protected_hashes',side_effect=hashes):
            with self.assertRaises(ValueError):w.prepare_host_session(self.f.repo,self.f.work,self.f.state,self.f.task(),now=100)
        self.assertEqual(self.f.store.db.execute("select status from development_jobs where id='next-a'").fetchone()[0],'blocked')
    def test_unreclaimed_expiry_never_dispatches(self):
        original=w.protected_hashes;called=[]
        def hashes(*args):
            value=original(*args);self.f.store.db.execute("update development_jobs set expires=0 where id='next-a'");return value
        with patch.object(w,'protected_hashes',side_effect=hashes):
            w.run_task(self.f.repo,self.f.work,self.f.state,self.f.task(),lambda *args:called.append(True))
        self.assertEqual(called,[])
    def test_corrupted_preparation_is_not_overwritten(self):
        original=w.protected_hashes
        def hashes(*args):
            value=original(*args);self.f.store.db.execute("update development_jobs set evidence=NULL where id='next-a'");return value
        with patch.object(w,'protected_hashes',side_effect=hashes):
            with self.assertRaises(ValueError):w.prepare_host_session(self.f.repo,self.f.work,self.f.state,self.f.task(),now=100)
        status,evidence=self.f.store.db.execute("select status,evidence from development_jobs where id='next-a'").fetchone()
        self.assertEqual(status,'running');self.assertIsNone(evidence)

if __name__=='__main__':unittest.main()

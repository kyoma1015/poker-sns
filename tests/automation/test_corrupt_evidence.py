"""Actual Leases with corrupt evidence in owned temporary SQLite only."""
from pathlib import Path
import concurrent.futures
import json
import multiprocessing
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import code_worker as w


def task(ident='old',lane='A'):
    return {'id':ident,'lane':lane,'base_sha':'a'*40,'branch':'codex/'+ident,
        'allowed_paths':['source.py'],'protected_tests':['tests/check.py'],
        'instruction':'owned fixture','test_profile':'python'}

def row(db):
    return db.execute("select id,lane,spec_hash,status,attempts,token,expires,evidence from development_jobs order by id").fetchall()

def child_claim(path,ident,lane):
    leases=w.Leases(path)
    try:return leases.claim(task(ident,lane),now=200) is not None
    finally:leases.close()

BAD=[('malformed','{'),('null',None),('jsonnull','null'),('bool','true'),('number','12'),
     ('string','"running"'),('array','[]'),('empty','{}'),
     ('missing_liveness','{"lease_evidence_version":1}'),
     ('missing_version','{"worker_liveness":"stopped"}'),
     ('unknown','{"lease_evidence_version":1,"worker_liveness":"unrecognized"}'),
     ('null_liveness','{"lease_evidence_version":1,"worker_liveness":null}'),
     ('flag_string','{"lease_evidence_version":1,"worker_liveness":"stopped","worker_liveness_unknown":"false"}'),
     ('duplicate','{"lease_evidence_version":1,"worker_liveness":"unknown","worker_liveness":"stopped"}'),
     ('nan','{"lease_evidence_version":1,"worker_liveness":"stopped","other":NaN}'),
     ('exponent','{"lease_evidence_version":1,"worker_liveness":"stopped","other":1e999}')]

class CorruptEvidence(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite';self.l=w.Leases(self.path)
        self.token=self.l.claim(task(),seconds=30,now=100)
    def tearDown(self):self.l.close();self.tmp.cleanup()
    def inject(self,value):self.l.db.execute("update development_jobs set evidence=? where id='old'",(value,))
    def test_bad_evidence_refuses_same_and_other_lane_without_any_row_change(self):
        for name,value in BAD:
            for lane in ['A','B']:
                self.l.db.execute("DELETE FROM development_jobs WHERE id<>'old'")
                self.l.db.execute("UPDATE development_jobs SET status='running',attempts=1,token=?,expires=130,evidence=? WHERE id='old'",(self.token,value))
                with self.subTest(value=name,lane=lane):
                    before=row(self.l.db)
                    claimed=self.l.claim(task('new-'+lane,lane),now=200)
                    # No token values are printed on assertion failure.
                    self.assertTrue(claimed is None,'unsafe claim succeeded for '+name+'/'+lane)
                    self.assertTrue(row(self.l.db)==before,'original row changed for '+name+'/'+lane)
    def test_bad_active_evidence_refuses_other_lane_before_expiry(self):
        self.inject(None);before=row(self.l.db)
        self.assertTrue(self.l.claim(task('new','B'),now=101) is None,'active NULL allowed another lane')
        self.assertTrue(row(self.l.db)==before)
    def test_expired_known_running_is_not_a_death_certificate(self):
        self.inject(json.dumps({'lease_evidence_version':1,'worker_liveness':'running'}));before=row(self.l.db)
        self.assertTrue(self.l.claim(task('new','B'),now=200) is None,'expired running was taken over')
        self.assertTrue(row(self.l.db)==before)
    def test_normal_claim_has_explicit_nonexecuting_evidence(self):
        raw=self.l.db.execute("select evidence from development_jobs where id='old'").fetchone()[0]
        self.assertTrue(isinstance(raw,str),'new claim has NULL evidence')
        value=json.loads(raw)
        self.assertEqual(value['lease_evidence_version'],1);self.assertEqual(value['worker_liveness'],'not_started')
    def test_normal_nonstarted_expiry_completion_and_retry_remain_bounded(self):
        self.assertTrue(self.l.claim(task('new','B'),now=200) is not None)
        self.assertEqual(self.l.db.execute("select status from development_jobs where id='old'").fetchone()[0],'blocked')
        for attempt in range(2):
            token=self.l.claim(task('retry','C'),now=201+attempt)
            self.assertTrue(token is not None)
            self.l.finish('retry',token,'retry_wait',{},now=201+attempt+.1)
        self.assertTrue(self.l.claim(task('retry','C'),now=204) is None)
        self.assertTrue(self.l.claim(task('new','B'),now=201) is None)
    def test_multiprocess_corrupt_expiry_has_zero_winners_and_preserves_row(self):
        self.inject('{');before=row(self.l.db)
        with concurrent.futures.ProcessPoolExecutor(max_workers=4,mp_context=multiprocessing.get_context('spawn')) as pool:
            futures=[pool.submit(child_claim,self.path,'child-'+str(i),'ABCD'[i%4]) for i in range(8)]
            self.assertEqual(sum(f.result(timeout=15) for f in futures),0)
        self.assertTrue(row(self.l.db)==before)
        self.assertEqual(self.l.db.execute('pragma integrity_check').fetchone()[0],'ok')
    def test_rollback_after_later_claim_validation_error_keeps_expired_row(self):
        # Valid expiry then invalid task access must roll back the expiry UPDATE.
        before=row(self.l.db)
        with self.assertRaises(KeyError):self.l.claim({'id':'new'},now=200)
        self.assertTrue(row(self.l.db)==before)
        self.assertFalse(self.l.db.in_transaction)
    def test_host_boundary_unknown_with_corrupt_context_refuses_new_claim(self):
        sys.path.insert(0,str(ROOT/'tests/worker_acceptance'))
        import test_continuation_recovery as fixture
        from invocation_guard import InvocationGuard
        f=fixture.RecoveryAcceptance();f.setUp()
        try:
            with InvocationGuard(f.store,'owned-run','/fixture',enabled=True) as guard:
                q=w.prepare_host_session(f.repo,f.work,f.state,f.task(),now=100)
                states=iter(['stopped','unknown'])
                def preserve(result,status):
                    f.store.db.execute("update development_jobs set evidence=NULL where id='next-a'")
                with self.assertRaises(w.WorkerLivenessUnknown):
                    guard.call_host(lambda:{'partial':'retained'},observe=lambda:next(states),preserve=preserve)
            before=row(f.store.db)
            self.assertTrue(f.store.leases.claim(f.task('next-b','B'),now=10000) is None)
            self.assertTrue(row(f.store.db)==before)
            with self.assertRaises(ValueError):
                with InvocationGuard(f.store,'no-takeover','/fixture',enabled=True):self.fail('unknown takeover')
        finally:f.tearDown()

if __name__=='__main__':unittest.main()

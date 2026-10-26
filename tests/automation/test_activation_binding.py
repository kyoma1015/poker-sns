"""Task identity must remain bound to an acquired activation, isolated state."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
import code_worker as w

def task(ident='owned',lane='A'):
    return {'id':ident,'lane':lane,'base_sha':'a'*40,'branch':'codex/'+ident,'instruction':'owned',
            'allowed_paths':['value.py'],'protected_tests':['test.py'],'test_profile':'python'}

def snapshot(db):return db.execute('select * from development_jobs order by id').fetchall()

class ActivationBinding(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.l=w.Leases(Path(self.tmp.name)/'state.sqlite');self.t=task();self.token=self.l.claim(self.t,now=100)
    def tearDown(self):self.l.close();self.tmp.cleanup()
    def refuse(self,context,token=None):
        before=snapshot(self.l.db)
        with self.assertRaises(w.LeaseActivationRefused):self.l.activate('owned',self.token if token is None else token,context,now=101)
        self.assertTrue(snapshot(self.l.db)==before,'original row was modified')
        self.assertFalse(self.l.db.in_transaction)
    def test_corrupt_row_spec_hash_refuses(self):
        self.l.db.execute("update development_jobs set spec_hash=? where id='owned'",('b'*64,));self.refuse({})
    def test_context_task_cannot_change_reviewed_instruction(self):
        changed=dict(self.t,instruction='different');self.refuse({'task':changed})
    def test_incoming_claimed_hash_cannot_replace_acquired_identity(self):
        self.refuse({'claimed_spec_hash':'b'*64})
    def test_mismatched_running_spec_blocks_other_lane_without_mutation(self):
        self.l.db.execute("update development_jobs set spec_hash=? where id='owned'",('b'*64,));before=snapshot(self.l.db)
        self.assertTrue(self.l.claim(task('other','B'),now=10000) is None,'mismatched task metadata was expired/taken over')
        self.assertTrue(snapshot(self.l.db)==before)
    def test_wrong_token_never_changes_row(self):self.refuse({},token='wrong-token')
    def test_retry_spec_mismatch_rolls_back(self):
        self.l.finish('owned',self.token,'retry_wait',{},now=101);before=snapshot(self.l.db)
        with self.assertRaises(ValueError):self.l.claim(dict(self.t,instruction='different'),now=102)
        self.assertTrue(snapshot(self.l.db)==before);self.assertFalse(self.l.db.in_transaction)
    def test_matching_task_context_and_normal_completion(self):
        self.l.activate('owned',self.token,{'task':self.t},now=101)
        self.l.finish('owned',self.token,'implemented',{},now=102)
        self.assertTrue(self.l.claim(task('next','B'),now=103) is not None)

if __name__=='__main__':unittest.main()

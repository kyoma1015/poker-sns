"""Acquired task binding must hold through completion; owned real SQLite/Git."""
from pathlib import Path
import json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as w
import test_continuation_recovery as fixture
class FinishBinding(unittest.TestCase):
 def test_finish_rejects_changed_spec_without_mutation(self):
  with tempfile.TemporaryDirectory() as d:
   l=w.Leases(Path(d)/'owned.sqlite');t={'id':'owned','lane':'A','instruction':'original'}
   try:
    token=l.claim(t,now=100);l.activate('owned',token,{},now=101)
    l.db.execute("update development_jobs set spec_hash=? where id='owned'",('b'*64,));before=l.db.execute('select * from development_jobs').fetchall()
    with self.assertRaises(ValueError):l.finish('owned',token,'implemented',{},now=102)
    self.assertTrue(l.db.execute('select * from development_jobs').fetchall()==before)
   finally:l.close()
 def test_host_context_task_mismatch_refuses_before_source_commit(self):
  f=fixture.RecoveryAcceptance();f.setUp()
  try:
   q=w.prepare_host_session(f.repo,f.work,f.state,f.task(),now=100)
   work=Path(q['worktree']);(work/'src/value.py').write_text('VALUE=2\n');(work/'extra.py').write_text('UNREVIEWED=True\n')
   raw=f.store.db.execute("select evidence from development_jobs where id='next-a'").fetchone()[0];context=json.loads(raw);context['task']['allowed_paths'].append('extra.py')
   f.store.db.execute("update development_jobs set evidence=? where id='next-a'",(json.dumps(context),));before=f.store.db.execute('select * from development_jobs').fetchall()
   with self.assertRaises(ValueError):w.finish_host_session(f.state,'next-a',q['lease_token'],{'task_id':'next-a','dispatch_source':'collaboration','completed':True,'agent_id':'/root/owned_fixture','test_fixture':True},now=101)
   self.assertTrue(f.store.db.execute('select * from development_jobs').fetchall()==before)
   self.assertEqual(fixture.git(work,'rev-parse','HEAD'),context['base_sha'])
  finally:f.tearDown()
if __name__=='__main__':unittest.main()

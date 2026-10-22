"""Public restart metadata, CAS and private-evidence redaction."""
from pathlib import Path
import concurrent.futures,json,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from code_worker import Leases
from continuation_recovery import Continuation
class PublicationCheckpoint(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'state.sqlite'
  task={'id':'seed','lane':'A','base_sha':'a'*40,'base_branch':'main','branch':'codex/seed','instruction':'test','allowed_paths':['source.py'],'protected_tests':['test.py'],'test_profile':'python'}
  l=Leases(self.path);t=l.claim(task,now=1);l.finish('seed',t,'implemented',{'commit':'b'*40,'token':'PRIVATE_MARKER','context':{'secret':'PRIVATE_MARKER'}},now=2)
  self.anchor={'seed':l.db.execute('SELECT spec_hash FROM development_jobs WHERE id=?',('seed',)).fetchone()[0]};l.close();self.store=Continuation(self.path,self.anchor)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def metadata(self):return {'source_commit':'b'*40,'head_commit':'c'*40,'branch':'codex/seed','pr_number':106,'ci_run_id':123,'ci_attempt':1,'ci_status':'in_progress','owner':'/root/host','run_id':'invocation-1','last_success':'draft_created','next_action':'await_ci','retry_count':0}
 def record(self,data=None,revision=0,now=10):return self.store.record_publication('seed',self.metadata() if data is None else data,expected_revision=revision,now=now)
 def test_public_checkpoint_initial_empty(self):self.assertEqual(self.store.public_checkpoint()['publications'],[])
 def test_restore_all_fields_and_private_redaction(self):
  row=self.record();self.assertEqual(row['revision'],1);self.assertEqual(row['updated_at'],10)
  for k,v in self.metadata().items():self.assertEqual(row[k],v)
  self.store.close();self.store=Continuation(self.path,self.anchor);p=self.store.public_checkpoint();self.assertEqual(p['publications'],[row]);self.assertNotIn('PRIVATE_MARKER',json.dumps(p));self.assertNotIn('token',row)
 def test_cas_and_clock_prevent_stale_overwrite(self):
  old=self.record();new=dict(self.metadata(),ci_status='success',last_success='ci_observed',next_action='discover_next')
  with self.assertRaises(ValueError):self.record(new,revision=0,now=11)
  with self.assertRaises(ValueError):self.record(new,revision=1,now=9)
  self.assertEqual(self.store.public_checkpoint()['publications'],[old]);self.assertEqual(self.record(new,revision=1,now=11)['revision'],2)
 def test_identity_and_source_match_required(self):
  for k,v in [('source_commit','d'*40),('retry_count',1)]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.record(dict(self.metadata(),**{k:v}))
  old=self.record()
  for k,v in [('branch','codex/other'),('pr_number',107)]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.record(dict(self.metadata(),**{k:v}),revision=1,now=11)
  self.assertEqual(self.store.public_checkpoint()['publications'],[old])
 def test_untrusted_extra_and_invalid_fields_rejected(self):
  for k,v in [('token','PRIVATE_MARKER'),('ci_status','PASS'),('pr_number',True),('ci_run_id',0),('ci_attempt',0),('head_commit','short'),('branch','codex/../bad'),('owner','bad\nowner'),('run_id','bad space'),('last_success','raw SQL'),('next_action','execute'),('retry_count',False)]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.record(dict(self.metadata(),**{k:v}))
  self.assertEqual(self.store.public_checkpoint()['publications'],[])
 def test_invalid_clock_or_revision_is_atomic(self):
  for now in (float('nan'),float('inf'),True,'10'):
   with self.subTest(now=now),self.assertRaises(ValueError):self.record(now=now)
  for revision in (True,-1,1.0):
   with self.subTest(revision=revision),self.assertRaises(ValueError):self.record(revision=revision)
  self.assertEqual(self.store.public_checkpoint()['publications'],[])
 def test_missing_or_running_job_not_publishable(self):
  with self.assertRaises(ValueError):self.store.record_publication('missing',self.metadata(),expected_revision=0,now=10)
  self.store.db.execute("UPDATE development_jobs SET status='running' WHERE id='seed'")
  with self.assertRaises(ValueError):self.record()
  self.assertEqual(self.store.public_checkpoint()['publications'],[])
 def test_concurrent_cas_only_one_wins(self):
  def run(_):
   s=Continuation(self.path,self.anchor)
   try:
    try:s.record_publication('seed',self.metadata(),expected_revision=0,now=10);return 'saved'
    except ValueError:return 'stale'
   finally:s.close()
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:r=list(pool.map(run,range(2)))
  self.assertEqual(sorted(r),['saved','stale']);self.assertEqual(self.store.public_checkpoint()['publications'][0]['revision'],1)
 def test_does_not_reserve_run_or_modify_jobs(self):
  before=self.store.db.execute('SELECT * FROM development_jobs').fetchall();self.record();self.assertEqual(self.store.db.execute('SELECT * FROM development_jobs').fetchall(),before);self.assertEqual(self.store.public_checkpoint()['run_count'],0)

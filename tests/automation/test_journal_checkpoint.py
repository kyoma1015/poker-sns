"""Trusted external CAS fixture, never a retained controller or receipt."""
import json,sqlite3,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'scripts'))
class PinFixture:
 def __init__(self,path):
  self.db=sqlite3.connect(path);self.db.execute('create table if not exists pin(id integer primary key,data text)');self.db.commit()
 def load(self):
  row=self.db.execute('select data from pin where id=1').fetchone();return json.loads(row[0]) if row else None
 def cas(self,old,new):
  self.db.execute('begin immediate')
  try:
   if self.load()!=old:self.db.rollback();return False
   self.db.execute('insert or replace into pin values(1,?)',(json.dumps(new),));self.db.commit();return True
  except BaseException:self.db.rollback();raise
class Checkpoint(unittest.TestCase):
 def setUp(self):
  from private_journal import PrivateJournal
  from journal_checkpoint import JournalCheckpoint
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.pin=PinFixture(self.root/'external.sqlite');self.j=PrivateJournal(self.root/'journal');self.make=lambda:JournalCheckpoint(self.j,load=self.pin.load,cas=self.pin.cas)
 def tearDown(self):self.pin.db.close();self.tmp.cleanup()
 def test_advance_then_restart_keeps_prior_payload(self):
  c=self.make();head=c.append({'phase':'one'},operation_id='owned-one');self.assertEqual(self.make().restore(),[{'phase':'one'}]);self.assertEqual(self.pin.load()['head'],head)
 def test_interrupted_before_publish_recovers_intent(self):
  c=self.make();original=self.j.append
  def death(*a,**k):raise InterruptedError('owned interruption')
  self.j.append=death
  with self.assertRaises(InterruptedError):c.append({'phase':'one'},operation_id='owned-one')
  self.j.append=original;self.assertEqual(self.make().restore(),[{'phase':'one'}])
 def test_interrupted_after_publish_recovers_without_duplicate(self):
  c=self.make();original=self.pin.cas
  def stop(old,new):
   if new['pending'] is None:raise InterruptedError('before pin finalization')
   return original(old,new)
  c.cas=stop
  with self.assertRaises(InterruptedError):c.append({'phase':'one'},operation_id='owned-one')
  self.assertEqual(self.make().restore(),[{'phase':'one'}]);self.assertEqual(len(list(self.j.path.glob('[0-9]*.json'))),1)
 def test_processdeath_and_fresh_process_restore(self):
  code="""import os,sys
sys.path[:0]=[sys.argv[1],sys.argv[2]]
from test_journal_checkpoint import PinFixture
from private_journal import PrivateJournal
from journal_checkpoint import JournalCheckpoint
pin=PinFixture(sys.argv[3]);j=PrivateJournal(sys.argv[4]);c=JournalCheckpoint(j,load=pin.load,cas=pin.cas)
if sys.argv[5]=='before':j.append=lambda *a,**k:os._exit(31)
if sys.argv[5]=='after':
 original=c.cas
 def cas(old,new):
  if new['pending'] is None:os._exit(32)
  return original(old,new)
 c.cas=cas
if sys.argv[5]=='restore':
 assert c.restore()==[{'phase':'one'}];assert pin.load()['pending'] is None
 c.append({'phase':'one'},operation_id='owned-one');assert len(list(j.path.glob('[0-9]*.json')))==1
else:c.append({'phase':'one'},operation_id='owned-one')
"""
  for phase,status in [('before',31),('after',32)]:
   with self.subTest(phase=phase):
    folder=self.root/phase;folder.mkdir();args=[sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(ROOT/'tests/automation'),str(folder/'pin.sqlite'),str(folder/'journal')]
    self.assertEqual(subprocess.run(args+[phase],timeout=5).returncode,status)
    self.assertEqual(subprocess.run(args+['restore'],timeout=5).returncode,0)
    self.assertEqual(subprocess.run(args+['restore'],timeout=5).returncode,0)
 def test_guarded_queue_resume_reuses_pin_without_resetting_budget(self):
  sys.path.insert(0,str(ROOT/'tests/worker_acceptance'))
  import code_worker as worker
  import test_continuation_recovery as fixture
  from invocation_guard import InvocationGuard
  from prepared_host_boundary import complete_prepared
  f=fixture.RecoveryAcceptance();f.setUp()
  try:
   f.store.restrict_remaining_runs(2)
   with InvocationGuard(f.store,'first','/fixture',enabled=True) as guard:
    q=worker.prepare_host_session(f.repo,f.work,f.state,f.task(),now=100);work=Path(q['worktree'])
    receipt={'task_id':'next-a','dispatch_source':'collaboration','completed':True,'agent_id':'/root/owned_fixture','test_fixture':True}
    def dispatch():(work/'src/value.py').write_text('VALUE=2\n');return receipt
    def preserve(result,status):
     self.make().append({'receipt':result,'status':status},operation_id='owned-receipt');f.state.with_suffix('.stop').write_text('stop')
    with self.assertRaises(RuntimeError):complete_prepared(guard,f.state,'next-a',q['lease_token'],dispatch=dispatch,observe=lambda:'stopped',preserve=preserve,enabled=True,now=101)
    f.store.defer_host('next-a',q['lease_token'],'transient',agent_stopped=True,now=102,retry_after=1)
   f.state.with_suffix('.stop').unlink()
   saved=self.make().restore()[-1]
   self.assertEqual(saved['status']['liveness'],'stopped')
   with InvocationGuard(f.store,'second','/fixture',enabled=True) as guard:
    q=f.store.resume_host('next-a',now=104)
    self.assertEqual((Path(q['worktree'])/'src/value.py').read_text(),'VALUE=2\n')
    result=complete_prepared(guard,f.state,'next-a',q['lease_token'],dispatch=lambda:saved['receipt'],observe=lambda:'stopped',preserve=lambda *a:None,enabled=True,now=105)
    self.assertEqual(result['status'],'implemented_local');self.assertFalse(result['real_ai_implementation'])
   self.assertEqual(f.store.public_checkpoint()['run_count'],2)
   with self.assertRaises(ValueError):
    with InvocationGuard(f.store,'third','/fixture',enabled=True):self.fail('budget reset')
  finally:f.tearDown()
 def test_malformed_trusted_state_refuses(self):
  for bad in [[],{'revision':True,'head':None,'pending':None},{'revision':1,'head':None,'pending':{'index':0,'digest':'0'*64,'payload':{}}}]:
   c=self.make();c.load=lambda:bad
   with self.assertRaises(ValueError):c.restore()
 def test_unknown_tail_refuses_instead_of_accepting(self):
  self.j.append({'untrusted':'tail'},expected_head=None)
  with self.assertRaises(ValueError):self.make().restore()
 def test_same_operation_retry_deduplicates_and_changed_payload_refuses(self):
  c=self.make();head=c.append({'phase':'one'},operation_id='owned-one')
  self.assertEqual(self.make().append({'phase':'one'},operation_id='owned-one'),head)
  with self.assertRaises(ValueError):self.make().append({'phase':'changed'},operation_id='owned-one')
  self.assertEqual(self.make().restore(),[{'phase':'one'}])
 def test_cas_failure_never_publishes(self):
  c=self.make();c.cas=lambda old,new:False
  with self.assertRaises(ValueError):c.append({'phase':'one'},operation_id='owned-one')
  self.assertEqual(self.j.read(expected_head=None),[])
if __name__=='__main__':unittest.main()

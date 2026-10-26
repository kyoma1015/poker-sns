"""Actual guarded prepared state/Git, synthetic callbacks only, never a model."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as w
from invocation_guard import InvocationGuard
import test_continuation_recovery as fixture
from prepared_host_boundary import complete_prepared

class PreparedBoundary(unittest.TestCase):
 def setUp(self):
  self.f=fixture.RecoveryAcceptance();self.f.setUp();self.saved=[];self.calls=0
 def tearDown(self):self.f.tearDown()
 def guard(self,ident='owned-run'):return InvocationGuard(self.f.store,ident,'/fixture',enabled=True)
 def dispatch(self):
  self.calls+=1;(self.work/'src/value.py').write_text('VALUE=2\n')
  return {'task_id':'next-a','dispatch_source':'collaboration','completed':True,'agent_id':'/root/owned_fixture','test_fixture':True}
 def preserve(self,result,status):self.saved.append((result,status))
 def call(self,g,**kw):
  args={'dispatch':self.dispatch,'observe':lambda:'stopped','preserve':self.preserve,'enabled':True,'now':101};args.update(kw)
  return complete_prepared(g,self.f.state,'next-a',self.q['lease_token'],**args)
 def prepare(self):
  self.q=w.prepare_host_session(self.f.repo,self.f.work,self.f.state,self.f.task(),now=100);self.work=Path(self.q['worktree'])
 def test_explicit_optin_and_active_guard_required(self):
  g=self.guard()
  with self.assertRaises(ValueError):complete_prepared(g,self.f.state,'missing','unused',dispatch=self.dispatch,observe=lambda:'stopped',preserve=self.preserve)
  self.assertEqual(self.calls,0)
 def test_real_finish_after_safe_callback(self):
  with self.guard() as g:
   self.prepare();result=self.call(g)
  self.assertEqual(result['status'],'implemented_local');self.assertFalse(result['real_ai_implementation']);self.assertEqual(len(self.saved),1)
  self.assertEqual(self.f.store.public_checkpoint()['run_count'],1)
 def test_stop_before_dispatch_preserves_prepared_row(self):
  with self.guard() as g:
   self.prepare();before=self.f.store.db.execute('select * from development_jobs order by id').fetchall();self.f.state.with_suffix('.stop').write_text('stop')
   with self.assertRaises(RuntimeError):self.call(g)
   self.assertEqual(self.calls,0);self.assertTrue(self.f.store.db.execute('select * from development_jobs order by id').fetchall()==before)
 def test_unknown_after_dispatch_retains_context_and_blocks_other_lane(self):
  with self.guard() as g:
   self.prepare();states=iter(['stopped','unknown'])
   with self.assertRaises(w.WorkerLivenessUnknown):self.call(g,observe=lambda:next(states))
  row=self.f.store.db.execute("select status,evidence from development_jobs where id='next-a'").fetchone()
  self.assertEqual(row[0],'running');context=json.loads(row[1]);self.assertTrue(context['worker_liveness_unknown']);self.assertEqual(context['worktree'],str(self.work))
  self.assertTrue(self.f.store.leases.claim(self.f.task('other','B'),now=10000) is None)
  self.assertEqual(len(self.saved),1);self.assertEqual((self.work/'src/value.py').read_text(),'VALUE=2\n')
 def test_wrong_token_never_dispatches(self):
  with self.guard() as g:
   self.prepare();before=self.f.store.db.execute('select * from development_jobs order by id').fetchall();self.q['lease_token']='wrong'
   with self.assertRaises(ValueError):self.call(g)
   self.assertEqual(self.calls,0);self.assertTrue(self.f.store.db.execute('select * from development_jobs order by id').fetchall()==before)
 def test_protected_drift_refuses_before_dispatch(self):
  with self.guard() as g:
   self.prepare();(self.work/self.f.task()['protected_tests'][0]).write_text('tampered')
   with self.assertRaises(ValueError):self.call(g)
   self.assertEqual(self.calls,0)
 def test_persistence_failure_refuses_finish_and_retains_unknown(self):
  def unavailable(*args):raise OSError('owned disk error')
  with self.guard() as g:
   self.prepare()
   with self.assertRaises(w.WorkerLivenessUnknown):self.call(g,preserve=unavailable)
  self.assertEqual(self.f.store.db.execute("select status from development_jobs where id='next-a'").fetchone()[0],'running')
  self.assertTrue(self.f.store.leases.claim(self.f.task('other','B'),now=10000) is None)
 def test_stop_saved_work_defer_resume_under_unchanged_cap(self):
  self.f.store.restrict_remaining_runs(2)
  with self.guard('first') as g:
   self.prepare()
   def stopped_dispatch():
    result=self.dispatch();self.f.state.with_suffix('.stop').write_text('stop');return result
   with self.assertRaises(RuntimeError):self.call(g,dispatch=stopped_dispatch)
   self.f.store.defer_host('next-a',self.q['lease_token'],'transient',agent_stopped=True,now=102,retry_after=1)
  self.f.state.with_suffix('.stop').unlink()
  with self.guard('second') as g:
   self.q=self.f.store.resume_host('next-a',now=104);self.work=Path(self.q['worktree']);result=self.call(g,now=105)
   self.assertEqual(result['status'],'implemented_local')
  self.assertEqual(self.f.store.public_checkpoint()['run_count'],2)
  with self.assertRaises(ValueError):
   with self.guard('third'):self.fail('finite cap reset')

if __name__=='__main__':unittest.main()

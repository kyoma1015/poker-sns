"""Private-file checkpoint + fresh Python adapter resume; never provider/model proof."""
from pathlib import Path
import json,os,subprocess,sys,unittest
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as w
from invocation_guard import InvocationGuard
from prepared_host_boundary import complete_prepared
import test_continuation_recovery as fixture
class DurableResume(unittest.TestCase):
 def test_saved_private_result_and_work_resume_without_run_reset(self):
  f=fixture.RecoveryAcceptance();f.setUp()
  try:
   f.store.restrict_remaining_runs(2);saved=f.root/'private-result.json'
   with InvocationGuard(f.store,'first','/fixture',enabled=True) as guard:
    q=w.prepare_host_session(f.repo,f.work,f.state,f.task(),now=100);work=Path(q['worktree'])
    receipt={'task_id':'next-a','dispatch_source':'collaboration','completed':True,'agent_id':'/root/owned_fixture','test_fixture':True}
    def dispatch():(work/'src/value.py').write_text('VALUE=2\n');return receipt
    def preserve(result,status):
     pending=saved.with_suffix('.pending')
     fd=os.open(pending,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
     with os.fdopen(fd,'w') as out:json.dump({'receipt':result,'status':status},out);out.flush();os.fsync(out.fileno())
     os.replace(pending,saved)
     dfd=os.open(saved.parent,os.O_DIRECTORY)
     try:os.fsync(dfd)
     finally:os.close(dfd)
     f.state.with_suffix('.stop').write_text('stop')
    with self.assertRaises(RuntimeError):complete_prepared(guard,f.state,'next-a',q['lease_token'],dispatch=dispatch,observe=lambda:'stopped',preserve=preserve,enabled=True,now=101)
    f.store.defer_host('next-a',q['lease_token'],'transient',agent_stopped=True,now=102,retry_after=1)
   f.state.with_suffix('.stop').unlink()
   code='''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from continuation_recovery import Continuation
from invocation_guard import InvocationGuard
from prepared_host_boundary import complete_prepared
c=Continuation(Path(sys.argv[2]),json.loads(sys.argv[3]))
try:
 saved=json.loads(Path(sys.argv[4]).read_text())
 assert saved['status']['liveness']=='stopped'
 try:
  with InvocationGuard(c,'first','/fixture',enabled=True):raise AssertionError('duplicate run')
 except ValueError:pass
 with InvocationGuard(c,'second','/fixture',enabled=True) as g:
  q=c.resume_host('next-a',now=104)
  assert (Path(q['worktree'])/'src/value.py').read_text()=='VALUE=2\\n'
  result=complete_prepared(g,c.path,'next-a',q['lease_token'],dispatch=lambda:saved['receipt'],observe=lambda:'stopped',preserve=lambda *args:None,enabled=True,now=105)
  assert result['status']=='implemented_local' and not result['real_ai_implementation']
 assert c.public_checkpoint()['run_count']==2
 try:
  with InvocationGuard(c,'third','/fixture',enabled=True):raise AssertionError('reset cap')
 except ValueError:pass
 print('private-checkpoint/restored-work/adapter-finish/run-id/cap:PASS')
finally:c.close()
'''
   result=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(f.state),json.dumps(f.anchor),str(saved)],capture_output=True,text=True,timeout=15,env=w.child_env())
   self.assertEqual(result.returncode,0,result.stderr);self.assertIn('cap:PASS',result.stdout)
  finally:f.tearDown()
if __name__=='__main__':unittest.main()

"""Private atomic callback checkpoint + fresh-process guard restart; fixtures only."""
from pathlib import Path
import json
import os
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
from invocation_guard import InvocationGuard
import test_continuation_recovery as fixture

class HostBoundaryRestart(unittest.TestCase):
    def test_post_call_stop_keeps_private_checkpoint_and_rejects_same_run_after_restart(self):
        f=fixture.RecoveryAcceptance();f.setUp()
        try:
            checkpoint=f.root/'private-checkpoint.json';partial=f.root/'uncommitted.py'
            f.store.restrict_remaining_runs(2)
            def dispatch():
                partial.write_text('VALUE=2\n');f.state.with_suffix('.stop').write_text('stop')
                return {'next':'verify_existing_work','source_sha':'a'*40}
            def preserve(result,status):
                pending=checkpoint.with_suffix('.pending')
                with pending.open('x') as stream:
                    json.dump({'result':result,'status':status},stream);stream.flush();os.fsync(stream.fileno())
                os.replace(pending,checkpoint)
                fd=os.open(str(checkpoint.parent),os.O_DIRECTORY)
                try:os.fsync(fd)
                finally:os.close(fd)
            with self.assertRaises(RuntimeError):
                with InvocationGuard(f.store,'preserved-run','/fixture',enabled=True) as guard:
                    guard.call_host(dispatch,observe=lambda:'stopped',preserve=preserve)
            f.state.with_suffix('.stop').unlink()
            # Fresh Python process, not an independent provider/model invocation.
            code='''import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from continuation_recovery import Continuation
from invocation_guard import InvocationGuard
c=Continuation(Path(sys.argv[2]),json.loads(sys.argv[3]))
try:
 data=json.loads(Path(sys.argv[4]).read_text())
 assert data['result']['next']=='verify_existing_work'
 assert Path(sys.argv[5]).read_text()=='VALUE=2\\n'
 try:
  with InvocationGuard(c,'preserved-run','/fixture',enabled=True):raise AssertionError('replayed')
 except ValueError:pass
 with InvocationGuard(c,'next-approved-fixture','/fixture',enabled=True):pass
 assert c.public_checkpoint()['run_count']==2
 try:
  with InvocationGuard(c,'over-cap','/fixture',enabled=True):raise AssertionError('cap reset')
 except ValueError:pass
 print('checkpoint-restored same-run-rejected next-approved-run cap-preserved')
finally:c.close()
'''
            r=subprocess.run([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(f.state),json.dumps(f.anchor),str(checkpoint),str(partial)],capture_output=True,text=True,timeout=10)
            self.assertEqual(r.returncode,0,r.stderr)
            self.assertIn('cap-preserved',r.stdout)
        finally:f.tearDown()

if __name__=='__main__':unittest.main()

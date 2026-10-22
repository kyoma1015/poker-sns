"""Bounded owned-process QA; controlled executables and synthetic controller state."""
import fcntl
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT/'tests/worker_acceptance')]
import code_worker as worker
from invocation_guard import InvocationGuard
import test_continuation_recovery as fixture


WATCHDOG = '''
import sys,os,json,time,fcntl,threading
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import code_worker as w
base=Path(sys.argv[2]);mode=sys.argv[3]
real=w.subprocess.Popen
def tracked(*a,**kw):
 p=real(*a,**kw)
 fcntl.fcntl(p.stdin.fileno(),fcntl.F_SETPIPE_SZ,4096)
 (base/'worker.pid').write_text(str(p.pid))
 return p
w.subprocess.Popen=tracked
executor=w.CodexExecutor(base/'owned-worker',base/'fixture-attestation.json')
def stop_check():
 if (base/'stop').exists():raise RuntimeError('owned stop')
executor.stop_check=stop_check
if mode=='stop':
 threading.Timer(.15,lambda:(base/'stop').write_text('stop')).start()
start=time.monotonic()
try:
 executor({'allowed_paths':['source.py'],'instruction':'あ'*6000},base,.25 if mode=='timeout' else 1.0)
 print(json.dumps({'unexpected_success':True}),flush=True)
except BaseException as error:
 print(json.dumps({'type':type(error).__name__,'message':str(error),'elapsed':time.monotonic()-start}),flush=True)
'''


class WorkerIOBounds(unittest.TestCase):
    def stdin_case(self, mode):
        with tempfile.TemporaryDirectory(prefix='owned-stdin-qa-') as directory:
            base = Path(directory)
            executable = base/'owned-worker'
            executable.write_text('#!'+sys.executable+'\nimport time\ntime.sleep(30)\n')
            executable.chmod(0o700)
            (base/'fixture-attestation.json').write_text(json.dumps({'auth_mode':'existing_chatgpt_subscription','owner_confirmed':True,'new_paid_services':False}))
            p = subprocess.Popen([sys.executable,'-B','-c',WATCHDOG,str(ROOT/'scripts'),str(base),mode],
                                 stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                                 env=worker.child_env(),start_new_session=True)
            try:
                try:
                    out,err=p.communicate(timeout=3)
                except subprocess.TimeoutExpired:
                    self.fail('stdin write outlived bounded watchdog')
                self.assertEqual(p.returncode,0,err)
                result=json.loads(out)
                self.assertEqual(result['type'],'RuntimeError')
                self.assertIn('owned stop' if mode=='stop' else 'time/output limit',result['message'])
                self.assertLess(result['elapsed'],2.5)
            finally:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGKILL)
                p.communicate(timeout=3)
                pidfile=base/'worker.pid'
                if pidfile.exists():
                    try:os.killpg(int(pidfile.read_text()),signal.SIGKILL)
                    except ProcessLookupError:pass

    def test_stdin_backpressure_obeys_timeout(self):
        self.stdin_case('timeout')

    def test_stdin_backpressure_observes_cooperative_stop(self):
        self.stdin_case('stop')

    def test_cleanup_permission_failure_is_bounded_and_preserves_primary(self):
        primary=subprocess.TimeoutExpired(['owned'],.1)
        waits=[]
        class Process:
            pid=99999999
            stdin=None
            stdout=io.BytesIO()
            stderr=io.BytesIO()
            returncode=None
            def communicate(self,**kw):raise primary
            def poll(self):return None
            def wait(self,timeout=None):
                waits.append(timeout)
                if timeout is None:raise AssertionError('unbounded wait')
                raise subprocess.TimeoutExpired(['owned'],timeout)
            def __enter__(self):return self
            def __exit__(self,*args):raise AssertionError('unbounded Popen context exit')
        with patch.object(worker.subprocess,'Popen',return_value=Process()),patch.object(worker.os,'killpg',side_effect=PermissionError('owned denied')):
            try:worker.command(['owned'],'.',timeout=.1)
            except BaseException as error:self.assertIs(error,primary)
            else:self.fail('cleanup must fail closed')
        self.assertTrue(getattr(primary,'worker_liveness_unknown',False))
        self.assertTrue(waits)
        self.assertTrue(all(type(x) in (int,float) and 0<x<=1 for x in waits))
        self.assertLessEqual(len(waits),2)

    def test_unknown_liveness_keeps_job_running_and_refuses_restart(self):
        f=fixture.RecoveryAcceptance();f.setUp()
        try:
            def unknown(task,worktree,timeout):
                error=RuntimeError('owned cleanup unconfirmed')
                error.worker_liveness_unknown=True
                raise error
            result=worker.run_task(f.repo,f.work,f.state,f.task(),unknown,timeout=1)
            self.assertEqual(result['status'],'blocked')
            self.assertEqual(f.store.db.execute("select status from development_jobs where id='next-a'").fetchone()[0],'running')
            with self.assertRaises(ValueError):
                with InvocationGuard(f.store,'no-takeover','/fixture',enabled=True):
                    self.fail('unknown worker resumed')
            self.assertEqual(f.store.public_checkpoint()['run_count'],0)
        finally:f.tearDown()

    def test_command_preserves_stdout_stderr_and_nonzero_contract(self):
        code='import sys;print("out");print("err",file=sys.stderr)'
        self.assertEqual(worker.command([sys.executable,'-B','-c',code],'.'),'out')
        self.assertEqual(worker.command([sys.executable,'-B','-c',code],'.',include_stderr=True),'out\nerr')
        with self.assertRaisesRegex(RuntimeError,'exited 7'):
            worker.command([sys.executable,'-B','-c','raise SystemExit(7)'],'.')


if __name__=='__main__':unittest.main()

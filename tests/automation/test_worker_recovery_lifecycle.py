"""Actual worker/controller APIs with OS processes; synthetic executors, never AI proof."""
from pathlib import Path
import json
import os
import signal
import selectors
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT / 'tests/worker_acceptance')]
import code_worker as worker
import continuation_recovery as recovery
from invocation_guard import InvocationGuard
import test_continuation_recovery as recovery_fixture


def live(pid):
    try:
        return Path('/proc', str(pid), 'stat').read_text().rsplit(')', 1)[1].split()[0] != 'Z'
    except FileNotFoundError:
        return False


def wait_dead(pid, seconds=2):
    deadline = time.monotonic() + seconds
    while live(pid) and time.monotonic() < deadline:
        time.sleep(.01)
    return not live(pid)


def kill_owned_group(pgid):
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        pass


class WorkerRecoveryLifecycle(unittest.TestCase):
    def setUp(self):
        self.f = recovery_fixture.RecoveryAcceptance()
        self.f.setUp()
        self.events = []
        self.groups = []

    def tearDown(self):
        for pgid in self.groups:
            kill_owned_group(pgid)
        if os.environ.get('ISSUE22_OWNED_QA_METRICS'):
            with open(os.environ['ISSUE22_OWNED_QA_METRICS'], 'a') as h:
                h.write(json.dumps({'case':self.id(),'events':self.events})+'\n')
        self.f.tearDown()

    def test_pr111_cleanup_failure_preserves_original_ddl_exception(self):
        original = RuntimeError('owned original DDL error')
        real = worker.Leases(self.f.state)
        class DB:
            def execute(self, *args):
                raise original
        class Lease:
            db = DB()
            def close(self):
                real.close()
                raise OSError('owned close error')
        try:
            with patch.object(recovery, 'Leases', return_value=Lease()):
                try:
                    recovery.Continuation(self.f.state, self.f.anchor)
                except BaseException as error:
                    self.assertIs(error, original, 'cleanup masked the original DDL exception')
                else:
                    self.fail('initialization must fail')
        finally:
            real.close()

    def test_executor_timeout_terminates_term_ignoring_descendant(self):
        # Controlled fake executable, not a Codex CLI probe or credential operation.
        stub = self.f.root / 'owned-executable'
        stub.write_text('#!' + sys.executable + '\n' + '''
import subprocess,sys,os,json,time
from pathlib import Path
sys.stdin.read()
child=subprocess.Popen([sys.executable,'-c',"import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);print('READY',flush=True);time.sleep(30)"],stdout=subprocess.PIPE,text=True)
assert child.stdout.readline().strip()=='READY'
Path('owned-pids.json').write_text(json.dumps({'leader':os.getpid(),'child':child.pid}))
while True:time.sleep(.1)
''')
        stub.chmod(0o700)
        attestation = self.f.root / 'fixture-attestation.json'
        attestation.write_text(json.dumps({'auth_mode':'existing_chatgpt_subscription','owner_confirmed':True,'new_paid_services':False}))
        executor = worker.CodexExecutor(stub, attestation)
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(RuntimeError, 'time/output limit'):
                executor(self.f.task(), self.f.root, timeout=.8)
            ids = json.loads((self.f.root / 'owned-pids.json').read_text())
            self.groups.append(ids['leader'])
            self.assertTrue(wait_dead(ids['leader']))
            child_stopped = wait_dead(ids['child'])
            self.events.append({'event':'executor_timeout','leader_pid':ids['leader'],
                                'child_pid':ids['child'],'child_stopped':child_stopped,
                                'seconds':time.monotonic()-started,
                                'child_reaped_by_this_controller':False})
            self.assertTrue(child_stopped, 'executor returned with a live descendant')
            self.assertLess(time.monotonic() - started, 8)
        finally:
            p = self.f.root / 'owned-pids.json'
            if p.exists():
                ids = json.loads(p.read_text()); kill_owned_group(ids['leader'])

    def test_stop_preserve_reopen_resume_commit_then_next_reviewed_task(self):
        f = self.f
        f.store.restrict_remaining_runs(2)
        fixture = 'from pathlib import Path;import time;Path("src/value.py").write_text("VALUE=2\\n");print("READY",flush=True);time.sleep(30)'
        with InvocationGuard(f.store, 'owned-run-1', '/fixture', enabled=True) as guard:
            prepared = worker.prepare_host_session(f.repo, f.work, f.state, f.task(), now=100)
            wt = Path(prepared['worktree'])
            p = subprocess.Popen([sys.executable, '-B', '-c', fixture], cwd=wt,
                                 env=worker.child_env(), stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, start_new_session=True)
            self.groups.append(p.pid)
            try:
                self.assertEqual(p.stdout.readline().strip(), 'READY')
                retained = (wt / 'src/value.py').read_bytes()
                f.state.with_suffix('.stop').write_text('owned stop')
                requested = time.monotonic()
                with self.assertRaises(RuntimeError):
                    guard.check()
                with self.assertRaises(ValueError):
                    f.store.defer_host('next-a', prepared['lease_token'], 'transient', agent_stopped=False, now=101)
                os.killpg(p.pid, signal.SIGTERM)
                p.communicate(timeout=3)
                self.assertEqual(p.returncode, -signal.SIGTERM)
                self.assertTrue(wait_dead(p.pid))
                self.assertLess(time.monotonic() - requested, 3)
                self.events.append({'event':'stop_to_exit','pid':p.pid,'exit_code':p.returncode,'seconds':time.monotonic()-requested})
                self.assertEqual(f.store.defer_host('next-a', prepared['lease_token'], 'transient', agent_stopped=True, now=101, retry_after=1)['status'], 'deferred')
            finally:
                if p.poll() is None:
                    kill_owned_group(p.pid); p.communicate(timeout=3)
        f.state.with_suffix('.stop').unlink()
        f.store.close(); f.store = recovery.Continuation(f.state, f.anchor)
        self.assertEqual(f.store.public_checkpoint()['run_count'], 1)
        self.assertIsNone(f.store.resume_host('next-a', now=101))
        with InvocationGuard(f.store, 'owned-run-2', '/fixture', enabled=True):
            resumed = f.store.resume_host('next-a', now=102)
            self.assertEqual(resumed['worktree'], str(wt))
            self.assertEqual((wt / 'src/value.py').read_bytes(), retained)
            result = worker.finish_host_session(f.state, 'next-a', resumed['lease_token'],
                {'task_id':'next-a','dispatch_source':'collaboration','completed':True,
                 'agent_id':'/root/owned_fixture','test_fixture':True}, now=103)
            self.assertEqual(result['status'], 'implemented_local')
            self.assertFalse(result['real_ai_implementation'])
            self.assertEqual(result['tests'][0]['test_count'], 1)
            self.assertIsNone(f.store.resume_host('next-a', now=104))
            self.assertEqual(worker.prepare_host_session(f.repo, f.work, f.state, f.task(), now=104)['status'], 'skipped_existing_lease_or_result')
            # Synthetic reviewed catalog only: no new real development descriptor.
            plan = f.store.plan([f.candidate('next-b', 'B')], f.observe(), f.repo, now=100)
            self.assertEqual([x['id'] for x in plan['manifest']['tasks']], ['next-b'])
            q = worker.prepare_host_session(f.repo, f.work, f.state, plan['manifest']['tasks'][0], now=104)
            (Path(q['worktree'])/'src/value.py').write_text('VALUE=2\n')
            next_result = worker.finish_host_session(f.state, 'next-b', q['lease_token'],
                {'task_id':'next-b','dispatch_source':'collaboration','completed':True,
                 'agent_id':'/root/owned_fixture','test_fixture':True}, now=105)
            self.assertEqual(next_result['status'], 'implemented_local')
            self.assertFalse(next_result['real_ai_implementation'])
        for run in ('owned-run-1', 'owned-run-3'):
            with self.assertRaises(ValueError):
                with InvocationGuard(f.store, run, '/fixture', enabled=True):
                    self.fail('duplicate or exhausted budget')
        self.assertEqual(f.store.public_checkpoint()['run_count'], 2)
        self.assertEqual(f.store.public_checkpoint()['run_limit'], 2)

    def test_permission_and_second_transient_require_review_not_budget_reset(self):
        f = self.f
        q = worker.prepare_host_session(f.repo, f.work, f.state, f.task(), now=100)
        f.store.defer_host('next-a', q['lease_token'], 'transient', agent_stopped=True, now=101, retry_after=1)
        resumed = f.store.resume_host('next-a', now=102)
        self.assertEqual(f.store.defer_host('next-a', resumed['lease_token'], 'transient', agent_stopped=True, now=103, retry_after=1)['status'], 'blocked')
        self.assertIsNone(f.store.resume_host('next-a', now=104))
        q = worker.prepare_host_session(f.repo, f.work, f.state, f.task('next-b','B'), now=100)
        self.assertEqual(f.store.defer_host('next-b', q['lease_token'], 'permission', agent_stopped=True, now=101)['status'], 'blocked')
        self.assertIsNone(f.store.resume_host('next-b', now=1000))
        q = worker.prepare_host_session(f.repo, f.work, f.state, f.task('next-c','C'), now=100)
        self.assertEqual(f.store.defer_host('next-c', q['lease_token'], 'authentication', agent_stopped=True, now=101)['status'], 'blocked')
        self.assertIsNone(f.store.resume_host('next-c', now=1000))

    def test_stop_before_entry_dispatches_no_worker_or_lease(self):
        f = self.f
        f.state.with_suffix('.stop').write_text('owned pre-entry stop')
        with self.assertRaises(RuntimeError):
            with InvocationGuard(f.store,'never-start','/fixture',enabled=True):
                self.fail('dispatch boundary crossed')
        self.assertEqual(f.store.public_checkpoint()['run_count'],0)
        self.assertFalse((f.work/'next-a').exists())
        self.assertIsNone(f.store.db.execute("select id from development_jobs where id='next-a'").fetchone())

    def test_ci_failure_metadata_retains_committed_source_until_new_observation(self):
        f = self.f
        task = f.task()
        q = worker.prepare_host_session(f.repo,f.work,f.state,task,now=100)
        (Path(q['worktree'])/'src/value.py').write_text('VALUE=2\n')
        result = worker.finish_host_session(f.state,'next-a',q['lease_token'],
            {'task_id':'next-a','dispatch_source':'collaboration','completed':True,
             'agent_id':'/root/owned_fixture','test_fixture':True},now=101)
        self.assertEqual(result['status'],'implemented_local')
        metadata = {'source_commit':result['commit'],'head_commit':result['commit'],
                    'branch':task['branch'],'pr_number':123,'ci_run_id':123,'ci_attempt':1,
                    'ci_status':'failure','owner':'/fixture','run_id':'fixture-ci',
                    'last_success':'ci_observed','next_action':'blocked','retry_count':0}
        f.store.record_publication('next-a',metadata,expected_revision=0,now=102)
        f.store.close(); f.store = recovery.Continuation(f.state,f.anchor)
        observed = f.store.public_checkpoint()['publications'][0]
        self.assertEqual((observed['ci_status'],observed['next_action']),('failure','blocked'))
        self.assertEqual(worker.prepare_host_session(f.repo,f.work,f.state,task,now=103)['status'],'skipped_existing_lease_or_result')
        metadata.update(ci_status='success',next_action='review',ci_attempt=2)
        f.store.record_publication('next-a',metadata,expected_revision=1,now=104)
        self.assertEqual(f.store.public_checkpoint()['publications'][0]['revision'],2)
        self.assertEqual(f.store.db.execute("select status,attempts from development_jobs where id='next-a'").fetchone(),('implemented',1))

    def test_pr111_probe_connection_failure_propagates_without_new_state(self):
        failure = OSError('owned connect failure')
        before = self.f.store.db.execute('select id,spec_hash,status from development_jobs').fetchall()
        with patch.object(recovery.sqlite3, 'connect', side_effect=failure):
            with self.assertRaises(OSError) as caught:
                recovery.Continuation(self.f.state, self.f.anchor)
        self.assertIs(caught.exception, failure)
        self.assertEqual(self.f.store.db.execute('select id,spec_hash,status from development_jobs').fetchall(), before)

    def test_controller_sigkill_keeps_partial_work_until_worker_liveness_confirmed(self):
        f = self.f
        f.store.restrict_remaining_runs(2)
        code = '''
import sys,json,subprocess,time,os
sys.path.insert(0,sys.argv[1])
from code_worker import prepare_host_session,child_env
from continuation_recovery import Continuation
from invocation_guard import InvocationGuard
c=Continuation(sys.argv[2],json.loads(sys.argv[3]))
with InvocationGuard(c,'dead-controller','/fixture',enabled=True):
 q=prepare_host_session(sys.argv[4],sys.argv[5],sys.argv[2],json.loads(sys.argv[6]),now=100)
 source='from pathlib import Path;import time;Path("src/value.py").write_text("VALUE=2\\\\n");print("READY",flush=True);time.sleep(30)'
 p=subprocess.Popen([sys.executable,'-B','-c',source],cwd=q['worktree'],env=child_env(),stdout=subprocess.PIPE,text=True,start_new_session=True)
 assert p.stdout.readline().strip()=='READY'
 print(json.dumps({'controller_pid':os.getpid(),'worker_pid':p.pid}),flush=True)
 while True:time.sleep(.1)
'''
        p = subprocess.Popen([sys.executable,'-B','-c',code,str(ROOT/'scripts'),str(f.state),json.dumps(f.anchor),str(f.repo),str(f.work),json.dumps(f.task())],
                             stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                             env=worker.child_env(),start_new_session=True)
        self.groups.append(p.pid)
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(p.stdout,selectors.EVENT_READ)
                self.assertTrue(sel.select(timeout=5),'controller startup timeout')
            ids = json.loads(p.stdout.readline())
            self.groups.append(ids['worker_pid'])
            # Waiting for inherited pipe EOF would wait for the surviving worker.
            os.kill(p.pid,signal.SIGKILL); p.wait(timeout=3)
            self.assertEqual(p.returncode,-signal.SIGKILL)
            self.assertTrue(live(ids['worker_pid']))
            f.store.close(); f.store = recovery.Continuation(f.state,f.anchor)
            with self.assertRaises(ValueError):
                with InvocationGuard(f.store,'unconfirmed-worker','/fixture',enabled=True):
                    self.fail('unknown-live worker taken over')
            self.assertEqual(f.store.public_checkpoint()['run_count'],1)
            stopped_at = time.monotonic()
            kill_owned_group(ids['worker_pid'])
            self.assertTrue(wait_dead(ids['worker_pid']))
            worker_stop_seconds = time.monotonic()-stopped_at
            p.communicate(timeout=3)
            token,context = f.store.db.execute("select token,evidence from development_jobs where id='next-a'").fetchone()
            wt = Path(json.loads(context)['worktree'])
            original = (wt/'src/value.py').read_bytes()
            self.assertEqual(original,b'VALUE=2\n')
            f.store.defer_host('next-a',token,'transient',agent_stopped=True,now=101,retry_after=1)
            with InvocationGuard(f.store,'recovery-controller','/fixture',enabled=True):
                q = f.store.resume_host('next-a',now=102)
                self.assertEqual((Path(q['worktree'])/'src/value.py').read_bytes(),original)
                result = worker.finish_host_session(f.state,'next-a',q['lease_token'],
                    {'task_id':'next-a','dispatch_source':'collaboration','completed':True,
                     'agent_id':'/root/owned_fixture','test_fixture':True},now=103)
                self.assertEqual(result['status'],'implemented_local')
                self.assertFalse(result['real_ai_implementation'])
            self.events.append({**ids,'controller_exit':p.returncode,'worker_stopped_after_confirmation':True,
                                'worker_stop_seconds':worker_stop_seconds,'run_count':2})
            self.assertEqual(f.store.public_checkpoint()['run_count'],2)
        finally:
            if 'ids' in locals():
                kill_owned_group(ids['worker_pid'])
            if p.poll() is None:
                kill_owned_group(p.pid);p.communicate(timeout=3)


if __name__ == '__main__':
    unittest.main()

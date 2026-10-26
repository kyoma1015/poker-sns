"""Independent process topology and cleanup fault-injection QA, not AI proof."""
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

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import code_worker as worker
from test_worker_io_bounds import WATCHDOG


@unittest.skipUnless(sys.platform=='linux','Linux /proc and fixture subreaper required')
class WorkerTreeBoundaries(unittest.TestCase):
    def test_parent_death_during_stdin_retains_file_and_unknown_worker(self):
        with tempfile.TemporaryDirectory(prefix='owned-stdin-death-') as directory:
            base=Path(directory);exe=base/'owned-worker'
            exe.write_text('#!'+sys.executable+'\nfrom pathlib import Path\nimport time\nPath("source.pending").write_text("uncommitted=1\\n");Path("source.pending").replace("source.py")\ntime.sleep(30)\n');exe.chmod(0o700)
            (base/'fixture-attestation.json').write_text(json.dumps({'auth_mode':'existing_chatgpt_subscription','owner_confirmed':True,'new_paid_services':False}))
            p=subprocess.Popen([sys.executable,'-B','-c',WATCHDOG,str(ROOT/'scripts'),str(base),'death'],
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                               env=worker.child_env(),start_new_session=True)
            pid=None
            try:
                deadline=time.monotonic()+2
                while not ((base/'worker.pid').exists() and (base/'source.py').exists()) and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue((base/'source.py').exists())
                pid=int((base/'worker.pid').read_text());retained=(base/'source.py').read_bytes()
                p.kill();p.wait(timeout=2)
                self.assertEqual(p.returncode,-signal.SIGKILL)
                state=Path('/proc',str(pid),'stat').read_text().rsplit(')',1)[1].split()[0]
                self.assertNotEqual(state,'Z')
                self.assertEqual((base/'source.py').read_bytes(),retained)
                # This is UNKNOWN until the owning coordinator confirms termination.
                if os.environ.get('ISSUE22_OWNED_TREE_METRICS'):
                    with open(os.environ['ISSUE22_OWNED_TREE_METRICS'],'a') as h:
                        h.write(json.dumps({'parent_pid':p.pid,'worker_pid':pid,'parent_exit':p.returncode,
                                            'checkpoint_preserved':True,'worker_liveness':'UNKNOWN'})+'\n')
            finally:
                if p.poll() is None:p.kill()
                if pid is not None:
                    try:os.killpg(pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                p.communicate(timeout=3)

    def probe(self,escaped):
        with tempfile.TemporaryDirectory(prefix='owned-tree-qa-') as directory:
            path=Path(directory)/'ids.json'
            p=subprocess.Popen([sys.executable,'-B',str(ROOT/'tests/automation/owned_tree_probe.py'),str(path),str(int(escaped))],
                               stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                               env=worker.child_env(),start_new_session=True)
            try:
                out,err=p.communicate(timeout=5)
                self.assertEqual(p.returncode,0,err)
                data=json.loads(out)
                self.assertEqual(data['child_reaped_signal'],signal.SIGKILL)
                self.assertEqual(data['grand_reaped_signal'],signal.SIGKILL)
                self.assertEqual(data['escaped_survived'],escaped)
                self.assertEqual(data['worker_liveness_unknown'],escaped)
                if escaped:self.assertEqual(data['automatic_full_tree_liveness'],'UNKNOWN')
                if os.environ.get('ISSUE22_OWNED_TREE_METRICS'):
                    with open(os.environ['ISSUE22_OWNED_TREE_METRICS'],'a') as h:h.write(json.dumps(data)+'\n')
            finally:
                if p.poll() is None:
                    os.killpg(p.pid,signal.SIGKILL)
                if path.exists():
                    for pid in json.loads(path.read_text()).values():
                        try:os.kill(pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                p.communicate(timeout=3)

    def test_same_group_child_and_grandchild_terminated_and_fixture_reaped(self):
        self.probe(False)

    def test_detached_session_survives_and_is_explicitly_unknown(self):
        self.probe(True)

    def test_real_wait_budget_under_injected_permission_failure(self):
        real=worker.subprocess.Popen;created=[]
        def tracked(*args,**kwargs):
            p=real(*args,**kwargs);created.append(p);return p
        started=time.monotonic()
        try:
            with patch.object(worker.subprocess,'Popen',side_effect=tracked),patch.object(worker.os,'killpg',side_effect=PermissionError('owned injected denial')):
                with self.assertRaises(subprocess.TimeoutExpired) as caught:
                    worker.command([sys.executable,'-B','-c','import time;time.sleep(30)'],'.',timeout=.1)
            self.assertTrue(caught.exception.worker_liveness_unknown)
            self.assertLess(time.monotonic()-started,2)
            self.assertIsNone(created[0].poll())
        finally:
            for p in created:
                p.kill();p.wait(timeout=2)


if __name__=='__main__':unittest.main()

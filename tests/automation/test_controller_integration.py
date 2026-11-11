"""Read-only integration gates using owned temporary SQLite/processes only."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from code_worker import Leases, setup_lock

IMPORT = "import sys;sys.path.insert(0,sys.argv[1]);from code_worker import Leases,setup_lock;"


class ControllerIntegration(unittest.TestCase):
    def test_bounded_lock_timeout_then_restart_preserves_committed_result(self):
        with tempfile.TemporaryDirectory(prefix='controller-main-timeout-') as directory:
            state = Path(directory) / 'owned.sqlite'
            task = {'id': 'owned-completed', 'lane': 'A'}
            leases = Leases(state)
            token = leases.claim(task, now=100)
            leases.finish(task['id'], token, 'implemented', {'owned': True}, now=101)
            leases.close()
            child = IMPORT + "\ntry:\n with setup_lock(sys.argv[2],seconds=.1):print('unexpected')\nexcept RuntimeError:print('bounded-timeout')\n"
            with setup_lock(state):
                result = subprocess.run([sys.executable, '-B', '-c', child, str(ROOT / 'scripts'), str(state)],
                                        capture_output=True, text=True, timeout=3)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), 'bounded-timeout')
            reopened = Leases(state)
            try:
                self.assertEqual(reopened.report()[0]['status'], 'implemented')
                self.assertIsNone(reopened.claim(task, now=102))
            finally:
                reopened.close()

    def test_process_exit_releases_os_lock_for_next_initializer(self):
        with tempfile.TemporaryDirectory(prefix='controller-main-crash-') as directory:
            state = Path(directory) / 'owned.sqlite'
            child = IMPORT + "\nimport os\nwith setup_lock(sys.argv[2]):os._exit(17)\n"
            result = subprocess.run([sys.executable, '-B', '-c', child, str(ROOT / 'scripts'), str(state)],
                                    capture_output=True, text=True, timeout=3)
            self.assertEqual(result.returncode, 17)
            reopened = Leases(state)
            try:
                self.assertEqual(reopened.report(), [])
            finally:
                reopened.close()


if __name__ == '__main__':
    unittest.main()

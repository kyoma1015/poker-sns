"""Real isolated SQLite/process regression, never the retained private state."""
import concurrent.futures
import importlib.util
from pathlib import Path
import select
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('init_worker', ROOT / 'scripts/code_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
CHILD = '''
import importlib.util,sys
spec=importlib.util.spec_from_file_location('child_worker',sys.argv[1])
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
print('starting',flush=True)
db=w.Leases(sys.argv[2])
print('ready',flush=True)
db.close()
'''


class LeaseInitialization(unittest.TestCase):
    def test_existing_cross_process_setup_exclusion_covers_state_initialization(self):
        with tempfile.TemporaryDirectory(prefix='pokerid-init-exclusion-') as directory:
            state = Path(directory) / 'owned.sqlite'
            child = None
            early = None
            try:
                with worker.setup_lock(state):
                    child = subprocess.Popen([sys.executable, '-B', '-c', CHILD,
                                              str(ROOT / 'scripts/code_worker.py'), str(state)],
                                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    self.assertTrue(select.select([child.stdout], [], [], 5)[0])
                    self.assertEqual(child.stdout.readline().strip(), 'starting')
                    # Parent intentionally holds the existing coordinator setup lock.
                    # A cooperating initializer cannot create/migrate the SQLite file yet.
                    early = bool(select.select([child.stdout], [], [], .25)[0])
                    created_while_locked = state.exists()
                out, err = child.communicate(timeout=5)
                self.assertEqual(child.returncode, 0, err)
                self.assertFalse(early, 'initializer bypassed the shared setup exclusion')
                self.assertFalse(created_while_locked, 'SQLite opened before setup guard released')
                self.assertIn('ready', out)
            finally:
                if child is not None and child.poll() is None:
                    child.kill(); child.communicate(timeout=5)

    def test_parallel_fresh_initializers_keep_wal_schema_and_all_rows(self):
        with tempfile.TemporaryDirectory(prefix='pokerid-init-parallel-') as directory:
            state = Path(directory) / 'owned.sqlite'
            def run(index):
                leases = worker.Leases(state)
                try:
                    task = {'id': 'owned-' + str(index), 'lane': str(index)}
                    return leases.claim(task, now=100) is not None
                finally:
                    leases.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
                self.assertEqual(list(pool.map(run, range(8))), [True] * 8)
            with sqlite3.connect(state) as db:
                self.assertEqual(db.execute('PRAGMA journal_mode').fetchone()[0], 'wal')
                self.assertEqual(db.execute('SELECT count(*) FROM development_jobs').fetchone()[0], 8)

    def test_initialization_failure_closes_connection_and_releases_setup_guard(self):
        with tempfile.TemporaryDirectory(prefix='pokerid-init-error-') as directory:
            state = Path(directory) / 'owned.sqlite'
            real_connect = sqlite3.connect
            opened = []
            class BrokenSchema:
                def __init__(self, *args, **kwargs):
                    self.inner = real_connect(*args, **kwargs); opened.append(self.inner)
                def execute(self, sql, *args):
                    if sql.startswith('CREATE TABLE'):
                        raise sqlite3.OperationalError('owned synthetic schema failure')
                    return self.inner.execute(sql, *args)
                def close(self):
                    self.inner.close()
            with patch.object(worker.sqlite3, 'connect', BrokenSchema):
                with self.assertRaises(sqlite3.OperationalError):
                    worker.Leases(state)
            try:
                with self.assertRaises(sqlite3.ProgrammingError):
                    opened[0].execute('SELECT 1')
            finally:
                opened[0].close()
            leases = worker.Leases(state)
            try:
                self.assertEqual(leases.report(), [])
            finally:
                leases.close()

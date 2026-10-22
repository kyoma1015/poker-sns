"""Pre-adoption integration QA; owned temporary databases only, never live state."""
from pathlib import Path
import hashlib
import json
import os
import selectors
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import continuation_recovery
from code_worker import Leases
from continuation_recovery import Continuation
from invocation_guard import InvocationGuard

TASK = dict(id='seed', lane='A', base_sha='a' * 40, base_branch='main',
            branch='codex/seed', instruction='fixture', allowed_paths=['source.py'],
            protected_tests=['test.py'], test_profile='python')
ANCHOR = {'seed': hashlib.sha256(json.dumps(TASK, sort_keys=True).encode()).hexdigest()}
META = dict(source_commit='b' * 40, head_commit='c' * 40, branch='codex/seed',
            pr_number=107, ci_run_id=123, ci_attempt=1, ci_status='success',
            owner='/fixture', run_id='fixture', last_success='ci_observed',
            next_action='review', retry_count=0)


def emit(value):
    print(json.dumps(value), flush=True)


def child(mode, path, ident):
    # Called only with a path created by this test's TemporaryDirectory.
    if mode == 'ddl':
        emit('ready'); sys.stdin.readline()
        s = Continuation(path, ANCHOR) if ident != 'lease' else Leases(path)
        try:
            emit({'ok': s.db.execute('pragma journal_mode').fetchone()[0] == 'wal'})
        finally:
            s.close()
        return
    c = Continuation(path, ANCHOR)
    try:
        if mode == 'cas':
            emit('ready'); sys.stdin.readline()
            try:
                c.record_publication('seed', META, expected_revision=0, now=10)
                emit('saved')
            except ValueError:
                emit('stale')
        elif mode == 'guard':
            with InvocationGuard(c, ident, '/fixture', enabled=True):
                emit('entered'); sys.stdin.readline()
        elif mode == 'uncommitted':
            c.db.execute('BEGIN IMMEDIATE')
            c.db.execute('UPDATE continuation_publications SET revision=99')
            emit('uncommitted'); sys.stdin.readline()
            c.db.execute('COMMIT')
    finally:
        c.close()


class ControllerIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='controller-owned-qa-')
        self.path = Path(self.tmp.name) / 'owned.sqlite'
        self.children = []
        l = Leases(self.path)
        try:
            token = l.claim(TASK, now=1)
            l.finish('seed', token, 'implemented', {'commit': 'b' * 40}, now=2)
        finally:
            l.close()

    def tearDown(self):
        for p in self.children:
            if p.poll() is None:
                p.kill()
            p.communicate(timeout=10)
        self.tmp.cleanup()

    def start(self, mode, ident='fixture'):
        # No inherited credentials or service/database environment.
        env = {k: os.environ[k] for k in ('PATH', 'SYSTEMROOT') if k in os.environ}
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        p = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
                              '--child', mode, str(self.path), ident],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True, env=env)
        self.children.append(p)
        return p

    def read(self, p):
        with selectors.DefaultSelector() as sel:
            sel.register(p.stdout, selectors.EVENT_READ)
            self.assertTrue(sel.select(timeout=15), 'bounded child response timeout')
        line = p.stdout.readline()
        self.assertTrue(line, 'child exited before response')
        return json.loads(line)

    def go(self, p):
        p.stdin.write('GO\n'); p.stdin.flush()

    def finish(self, p):
        out, err = p.communicate(timeout=15)
        self.assertEqual(p.returncode, 0, err)
        return out

    def test_mixed_wal_bootstrap_and_controller_ddl_eight_processes(self):
        # Return the seeded database to DELETE before racing the WAL transition.
        db = sqlite3.connect(self.path)
        self.assertEqual(db.execute('pragma journal_mode=DELETE').fetchone()[0], 'delete')
        db.close()
        procs = [self.start('ddl', 'lease' if i % 2 else 'controller') for i in range(8)]
        for p in procs:
            self.assertEqual(self.read(p), 'ready')
        for p in procs:
            self.go(p)
        for p in procs:
            self.assertEqual(self.read(p), {'ok': True}); self.finish(p)
        c = Continuation(self.path, ANCHOR)
        try:
            self.assertEqual(c.db.execute('pragma integrity_check').fetchone()[0], 'ok')
            self.assertEqual(c.public_checkpoint()['run_count'], 0)
            tables = {r[0] for r in c.db.execute("select name from sqlite_master where type='table'")}
            self.assertTrue({'continuation_publications', 'continuation_runs', 'continuation_limits',
                             'continuation_candidates', 'continuation_failures',
                             'continuation_discoveries', 'development_jobs'} <= tables)
        finally:
            c.close()

    def test_cross_process_publication_cas_one_winner(self):
        procs = [self.start('cas', str(i)) for i in range(4)]
        for p in procs:
            self.assertEqual(self.read(p), 'ready')
        for p in procs:
            self.go(p)
        results = [self.read(p) for p in procs]
        for p in procs:
            self.finish(p)
        self.assertEqual(sorted(results), ['saved', 'stale', 'stale', 'stale'])
        c = Continuation(self.path, ANCHOR)
        try:
            self.assertEqual(c.public_checkpoint()['publications'][0]['revision'], 1)
        finally:
            c.close()

    def test_controller_ddl_failure_closes_connection_and_restart_preserves_jobs(self):
        opened = []
        class FailedDDL:
            def __init__(self, inner):
                self.inner = inner
            def execute(self, sql, *args):
                if 'CREATE TABLE IF NOT EXISTS continuation_publications' in sql:
                    raise sqlite3.OperationalError('owned controller DDL failure')
                return self.inner.execute(sql, *args)
            def close(self):
                self.inner.close()
        class FailingLeases(Leases):
            def __init__(self, path):
                super().__init__(path)
                opened.append(self.db)
                self.db = FailedDDL(self.db)
        try:
            with patch.object(continuation_recovery, 'Leases', FailingLeases):
                with self.assertRaisesRegex(sqlite3.OperationalError, 'owned controller DDL failure'):
                    Continuation(self.path, ANCHOR)
            with self.assertRaises(sqlite3.ProgrammingError):
                opened[0].execute('SELECT 1')
        finally:
            for db in opened:
                db.close()
        c = Continuation(self.path, ANCHOR)
        try:
            self.assertEqual(c.public_checkpoint()['run_count'], 0)
            self.assertEqual(c.db.execute("select spec_hash,status,attempts from development_jobs where id='seed'").fetchone(), (ANCHOR['seed'], 'implemented', 1))
            self.assertEqual(c.public_checkpoint()['publications'], [])
        finally:
            c.close()

    def test_publication_sql_failure_rolls_back_and_connection_recovers(self):
        c = Continuation(self.path, ANCHOR)
        try:
            first = c.record_publication('seed', META, expected_revision=0, now=10)
            c.db.execute("CREATE TEMP TRIGGER fail_update AFTER UPDATE ON continuation_publications BEGIN SELECT RAISE(ABORT,'fixture failure'); END")
            with self.assertRaises(sqlite3.IntegrityError):
                c.record_publication('seed', META, expected_revision=1, now=11)
            self.assertFalse(c.db.in_transaction)
            self.assertEqual(c.public_checkpoint()['publications'], [first])
            c.db.execute('DROP TRIGGER fail_update')
            self.assertEqual(c.record_publication('seed', META, expected_revision=1, now=11)['revision'], 2)
        finally:
            c.close()

    def test_same_run_live_exclusion_then_restart_replay_rejected(self):
        p = self.start('guard', 'same-run')
        self.assertEqual(self.read(p), 'entered')
        c = Continuation(self.path, ANCHOR)
        try:
            with self.assertRaises(TimeoutError):
                with InvocationGuard(c, 'same-run', '/fixture', enabled=True):
                    self.fail('concurrent entry')
            self.assertEqual(c.public_checkpoint()['run_count'], 1)
        finally:
            c.close()
        self.go(p); self.finish(p)
        c = Continuation(self.path, ANCHOR)
        try:
            with self.assertRaises(ValueError):
                with InvocationGuard(c, 'same-run', '/fixture', enabled=True):
                    self.fail('duplicate restart')
            with InvocationGuard(c, 'new-run', '/fixture', enabled=True):
                pass
            self.assertIsNone(c.leases.claim(TASK, now=3))
            self.assertEqual(c.db.execute("select status,attempts from development_jobs where id='seed'").fetchone(), ('implemented', 1))
        finally:
            c.close()

    def test_stop_arrives_between_reservation_and_entry_check(self):
        c = Continuation(self.path, ANCHOR)
        try:
            reserve = c.reserve_run
            def stopped(ident):
                result = reserve(ident)
                self.path.with_suffix('.stop').write_text('fixture stop')
                return result
            with patch.object(c, 'reserve_run', stopped), self.assertRaises(RuntimeError):
                with InvocationGuard(c, 'stop-race', '/fixture', enabled=True):
                    self.fail('body must not begin')
            self.assertEqual(c.public_checkpoint()['run_count'], 1)
            self.path.with_suffix('.stop').unlink()
            with self.assertRaises(ValueError):
                with InvocationGuard(c, 'stop-race', '/fixture', enabled=True):
                    self.fail('consumed run replay')
            with InvocationGuard(c, 'after-stop', '/fixture', enabled=True):
                pass
        finally:
            c.close()

    def test_during_stop_check_prevents_next_cooperative_step(self):
        c = Continuation(self.path, ANCHOR)
        steps = []
        try:
            with self.assertRaises(RuntimeError):
                with InvocationGuard(c, 'cooperative', '/fixture', enabled=True) as guard:
                    steps.append('before')
                    self.path.with_suffix('.stop').write_text('fixture stop')
                    guard.check()
                    steps.append('after')
            self.assertEqual(steps, ['before'])
        finally:
            c.close()

    def test_process_death_releases_lock_preserves_budget_and_unknown_job(self):
        p = self.start('guard', 'killed-run')
        self.assertEqual(self.read(p), 'entered')
        p.kill(); p.communicate(timeout=10)
        c = Continuation(self.path, ANCHOR)
        try:
            self.assertEqual(c.public_checkpoint()['run_count'], 1)
            with self.assertRaises(ValueError):
                with InvocationGuard(c, 'killed-run', '/fixture', enabled=True):
                    self.fail('replayed killed run')
            c.db.execute("UPDATE development_jobs SET status='running',expires=0 WHERE id='seed'")
            with self.assertRaises(ValueError):
                with InvocationGuard(c, 'unknown-live', '/fixture', enabled=True):
                    self.fail('stole unknown job')
            self.assertEqual(c.db.execute("select status from development_jobs where id='seed'").fetchone()[0], 'running')
            self.assertEqual(c.public_checkpoint()['run_count'], 1)
        finally:
            c.close()

    def test_process_death_rolls_back_uncommitted_checkpoint(self):
        c = Continuation(self.path, ANCHOR)
        first = c.record_publication('seed', META, expected_revision=0, now=10)
        c.close()
        p = self.start('uncommitted')
        self.assertEqual(self.read(p), 'uncommitted')
        p.kill(); p.communicate(timeout=10)
        c = Continuation(self.path, ANCHOR)
        try:
            self.assertEqual(c.public_checkpoint()['publications'], [first])
            self.assertEqual(c.db.execute('pragma integrity_check').fetchone()[0], 'ok')
            self.assertEqual(c.record_publication('seed', META, expected_revision=1, now=11)['revision'], 2)
        finally:
            c.close()


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--child':
        child(*sys.argv[2:])
    else:
        unittest.main()

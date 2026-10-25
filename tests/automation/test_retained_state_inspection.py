"""Owned temporary state only; never opens the retained Issue22 database."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))


class RetainedInspection(unittest.TestCase):
    def setUp(self):
        import inspect_retained_state as module
        self.module = module
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / 'state.sqlite'
        self.manifest = self.root / 'manifest.json'
        self.checkpoint = self.root / 'checkpoint.json'
        self.expected = self.root / 'expected.json'
        self.tasks = [{'id': f'job-{n}', 'lane': lane} for n, lane in enumerate('ABCD')]
        self.manifest.write_text(json.dumps({'tasks': self.tasks}))
        self.checkpoint.write_text('{"checkpoint":"synthetic"}')
        db = sqlite3.connect(self.state)
        db.executescript('''CREATE TABLE development_jobs (
          id TEXT PRIMARY KEY,lane TEXT,spec_hash TEXT,status TEXT,attempts INTEGER,
          token TEXT,expires REAL,evidence TEXT);
          CREATE TABLE continuation_runs (id TEXT PRIMARY KEY);
          CREATE TABLE continuation_limits (id INTEGER PRIMARY KEY,run_limit INTEGER);
          INSERT INTO continuation_runs VALUES('synthetic-run');
          INSERT INTO continuation_limits VALUES(1,2);''')
        for task in self.tasks:
            digest = hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()
            db.execute('INSERT INTO development_jobs VALUES(?,?,?,?,?,?,?,?)',
                       (task['id'], task['lane'], digest, 'implemented', 1,
                        'PRIVATE_TOKEN_SENTINEL', 2.0, 'PRIVATE_EVIDENCE_SENTINEL'))
        db.commit()
        self.reference = self.manual(db)
        db.close()
        self.expected.write_text(json.dumps(self.reference))

    def manual(self, db):
        rows = db.execute('select * from development_jobs order by id').fetchall()
        original = []
        for task in self.tasks:
            row = db.execute('select spec_hash,status from development_jobs where id=?', (task['id'],)).fetchone()
            original.append({'id': task['id'], 'match': row[0] == hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest(), 'status': row[1]})
        return {'total': len(rows), 'counts': dict(db.execute('select status,count(*) from development_jobs group by status')),
                'full_rows_digest': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
                'run_count': db.execute('select count(*) from continuation_runs').fetchone()[0],
                'run_limit': db.execute('select run_limit from continuation_limits').fetchone()[0],
                'original4': original, 'checkpoint_sha256': hashlib.sha256(self.checkpoint.read_bytes()).hexdigest()}

    def inspect(self):
        return self.module.inspect_retained_state(self.state, self.manifest, self.checkpoint, self.expected)

    def rejected(self):
        with self.assertRaises(self.module.InspectionError):
            self.inspect()

    def test_exact_manual_digest_and_no_database_content_change(self):
        before = self.state.read_bytes()
        self.assertEqual(self.inspect(), self.reference)
        self.assertEqual(before, self.state.read_bytes())
        self.assertNotIn('PRIVATE_', json.dumps(self.inspect()))

    def test_mode_ro_and_query_only_are_used(self):
        connect = sqlite3.connect
        calls, statements = [], []
        def observed(*args, **kwargs):
            calls.append((args, kwargs))
            db = connect(*args, **kwargs)
            db.set_trace_callback(statements.append)
            return db
        with patch.object(self.module.sqlite3, 'connect', side_effect=observed):
            self.inspect()
        self.assertIn('mode=ro', calls[0][0][0])
        self.assertIs(calls[0][1]['uri'], True)
        self.assertIn('PRAGMA query_only=ON', statements)
        self.assertFalse(any(s.upper().startswith(('CREATE', 'INSERT', 'UPDATE', 'DELETE')) for s in statements))

    def test_missing_database_is_not_created(self):
        self.state.unlink()
        self.rejected()
        self.assertFalse(self.state.exists())

    def test_manifest_duplicate_keys_nonfinite_and_duplicate_ids_refuse(self):
        for raw in ['{"tasks":[],"tasks":[]}', '{"tasks":NaN}', '{"tasks":1e999}', json.dumps({'tasks': [self.tasks[0]] * 4})]:
            with self.subTest(raw=raw):
                self.manifest.write_text(raw)
                self.rejected()

    def test_expected_duplicate_keys_nonfinite_and_wrong_shape_refuse(self):
        for raw in ['{"total":4,"total":4}', '{"total":Infinity}', '{"total":1e999}', '[]']:
            with self.subTest(raw=raw):
                self.expected.write_text(raw)
                self.rejected()

    def test_corrupt_database_refuses_without_repair(self):
        raw = b'PRIVATE_CORRUPT_SENTINEL'
        self.state.write_bytes(raw)
        self.rejected()
        self.assertEqual(self.state.read_bytes(), raw)

    def test_missing_schema_refuses_without_creating_tables(self):
        db = sqlite3.connect(self.state)
        db.execute('DROP TABLE continuation_runs'); db.commit(); db.close()
        self.rejected()
        db = sqlite3.connect(self.state)
        self.assertIsNone(db.execute("select name from sqlite_master where name='continuation_runs'").fetchone())
        db.close()

    def test_full_row_digest_detects_private_field_change(self):
        db = sqlite3.connect(self.state)
        db.execute("UPDATE development_jobs SET evidence='changed' WHERE id='job-0'"); db.commit(); db.close()
        self.rejected()

    def test_count_and_finite_run_budget_mismatch_refuse(self):
        for key, value in [('total', 5), ('run_count', 2), ('run_limit', 3), ('counts', {'implemented': 3, 'running': 1})]:
            expected = dict(self.reference); expected[key] = value
            self.expected.write_text(json.dumps(expected))
            with self.subTest(key=key): self.rejected()
        malformed = dict(self.reference)
        malformed['original4'] = [dict(row, match=1) for row in self.reference['original4']]
        self.expected.write_text(json.dumps(malformed))
        self.rejected()

    def test_original_task_hash_and_checkpoint_mismatch_refuse(self):
        db = sqlite3.connect(self.state)
        db.execute("UPDATE development_jobs SET spec_hash=? WHERE id='job-0'", ('0' * 64,)); db.commit(); db.close()
        self.rejected()
        db = sqlite3.connect(self.state)
        db.execute('UPDATE development_jobs SET spec_hash=? WHERE id=?', (hashlib.sha256(json.dumps(self.tasks[0], sort_keys=True).encode()).hexdigest(), 'job-0'))
        db.commit(); db.close()
        self.checkpoint.write_text('different')
        self.rejected()

    def test_actual_cli_sanitized_success_and_failure(self):
        command = [sys.executable, '-B', str(ROOT / 'scripts/inspect_retained_state.py'), '--state', str(self.state), '--manifest', str(self.manifest), '--checkpoint', str(self.checkpoint), '--expected', str(self.expected)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        output = json.loads(result.stdout)
        self.assertEqual(output['observed'], self.reference)
        self.assertIs(output['execution_allowed'], False)
        self.assertEqual(result.stderr, '')
        self.state.write_bytes(b'PRIVATE_CORRUPT_SENTINEL')
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['verdict'], 'BLOCKED')
        self.assertNotIn('PRIVATE_', result.stdout + result.stderr)
        self.assertNotIn(str(self.root), result.stdout + result.stderr)

    def test_reads_committed_wal_and_rejects_database_symlink(self):
        db = sqlite3.connect(self.state)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute("UPDATE development_jobs SET attempts=2 WHERE id='job-0'"); db.commit()
        expected = self.manual(db); self.expected.write_text(json.dumps(expected))
        before = self.state.read_bytes(), Path(str(self.state) + '-wal').read_bytes()
        self.assertEqual(self.inspect(), expected)
        self.assertEqual(before, (self.state.read_bytes(), Path(str(self.state) + '-wal').read_bytes()))
        db.close()
        target = self.root / 'target.sqlite'; self.state.rename(target); self.state.symlink_to(target)
        self.rejected()


if __name__ == '__main__':
    unittest.main()

"""Bounded four-lane queue primitives. No shell, network, production or AI calls.

A successful validation run is NOT completion of a development task.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sqlite3
import time
import uuid

LANES = ('A', 'B', 'C', 'D')


def validate_manifest(manifest):
    if manifest.get('version') != 1 or manifest.get('mode') != 'validation_only':
        raise ValueError('only version 1 validation_only mode is supported')
    if manifest.get('code_worker_configured') is not False:
        raise ValueError('an autonomous code worker has not been configured')
    if not 1 <= manifest.get('max_tasks_per_run', 0) <= 4:
        raise ValueError('max_tasks_per_run must be 1..4')
    if not 1 <= manifest.get('max_attempts', 0) <= 3:
        raise ValueError('max_attempts must be 1..3')
    if not 30 <= manifest.get('lease_seconds', 0) <= 3600:
        raise ValueError('lease_seconds must be 30..3600')
    tasks = manifest.get('tasks')
    if not isinstance(tasks, list) or len(tasks) > 100:
        raise ValueError('tasks must be a bounded list')
    ids = set()
    for task in tasks:
        task_id = task.get('id')
        if not isinstance(task_id, str) or not task_id or len(task_id) > 100 or task_id in ids:
            raise ValueError('task IDs must be unique nonempty strings')
        ids.add(task_id)
        if task.get('lane') not in LANES or task.get('kind') not in ('development', 'validation'):
            raise ValueError('invalid lane or task kind')
        if not isinstance(task.get('acceptance'), str) or not task['acceptance'].strip():
            raise ValueError('acceptance criteria required')
        if 'command' in task or 'shell' in task:
            raise ValueError('queue data cannot supply executable commands')
    return manifest


class Queue:
    def __init__(self, path, manifest):
        self.manifest = validate_manifest(manifest)
        self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
        self.db.execute('PRAGMA busy_timeout=10000')
        self.db.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY, lane TEXT NOT NULL, kind TEXT NOT NULL,
            spec_hash TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'queued',
            attempts INTEGER NOT NULL DEFAULT 0, token TEXT, expires REAL,
            retry_at REAL NOT NULL DEFAULT 0, evidence TEXT)''')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            for task in manifest['tasks']:
                digest = hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()
                old = self.db.execute('SELECT spec_hash FROM tasks WHERE id=?', (task['id'],)).fetchone()
                if old and old[0] != digest:
                    raise ValueError('task changed without a new immutable ID: ' + task['id'])
                self.db.execute('INSERT OR IGNORE INTO tasks(id,lane,kind,spec_hash) VALUES(?,?,?,?)',
                                (task['id'], task['lane'], task['kind'], digest))
            active_ids = [task['id'] for task in manifest['tasks']]
            if active_ids:
                slots = ','.join('?' for _ in active_ids)
                self.db.execute(f"UPDATE tasks SET status='blocked',token=NULL,evidence='task removed from manifest' WHERE id NOT IN ({slots}) AND status!='succeeded'", active_ids)
            else:
                self.db.execute("UPDATE tasks SET status='blocked',token=NULL,evidence='task removed from manifest' WHERE status!='succeeded'")
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            self.db.close()
            raise

    def close(self):
        self.db.close()

    def claim(self, lane, now=None):
        if lane not in LANES:
            raise ValueError('invalid lane')
        now = time.time() if now is None else now
        self.db.execute('BEGIN IMMEDIATE')
        try:
            # Expiry is a hard stop: never duplicate work by silently stealing a lease.
            self.db.execute("UPDATE tasks SET status='blocked',token=NULL,evidence='lease expired; operator review required' WHERE status='running' AND expires<=?", (now,))
            active = self.db.execute("SELECT 1 FROM tasks WHERE lane=? AND status='running'", (lane,)).fetchone()
            row = None if active else self.db.execute("SELECT id FROM tasks WHERE lane=? AND kind='validation' AND status IN ('queued','retry_wait') AND retry_at<=? AND attempts<? ORDER BY rowid LIMIT 1",
                       (lane, now, self.manifest['max_attempts'])).fetchone()
            result = None
            if row:
                token = uuid.uuid4().hex
                expires = now + self.manifest['lease_seconds']
                self.db.execute("UPDATE tasks SET status='running', attempts=attempts+1,token=?,expires=? WHERE id=?", (token, expires, row[0]))
                result = {'id': row[0], 'lane': lane, 'token': token, 'expires': expires}
            self.db.execute('COMMIT')
            return result
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def finish(self, task_id, token, success, evidence, now=None):
        if not isinstance(evidence, str) or not evidence.strip() or len(evidence) > 2000:
            raise ValueError('bounded evidence reference required')
        now = time.time() if now is None else now
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self.db.execute("SELECT attempts,expires FROM tasks WHERE id=? AND token=? AND status='running'", (task_id, token)).fetchone()
            if row is None or row[1] <= now:
                raise ValueError('invalid or expired lease')
            status = 'succeeded' if success else ('failed' if row[0] >= self.manifest['max_attempts'] else 'retry_wait')
            retry_at = 0 if success else now + min(3600, 60 * 2 ** (row[0] - 1))
            self.db.execute('UPDATE tasks SET status=?,token=NULL,expires=NULL,retry_at=?,evidence=? WHERE id=?',
                            (status, retry_at, evidence, task_id))
            self.db.execute('COMMIT')
            return status
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def report(self):
        rows = self.db.execute('SELECT id,lane,kind,status,attempts,evidence FROM tasks ORDER BY rowid').fetchall()
        return {'mode': 'validation_only', 'autonomous_development_running': False,
                'tasks': [dict(zip(('id', 'lane', 'kind', 'status', 'attempts', 'evidence'), row)) for row in rows]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, default=Path('.github/queues/development.json'))
    parser.add_argument('--state', type=Path, required=True, help='ephemeral local SQLite; never a production connection')
    parser.add_argument('--lane', choices=LANES)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    queue = Queue(args.state, manifest)
    try:
        if args.lane:
            # Output a plan only; no task command or code-writing worker is invoked.
            plan = [t for t in manifest['tasks'] if t['lane'] == args.lane]
            print(json.dumps({'lane': args.lane, 'execution': 'plan_only', 'code_worker_configured': False,
                              'max_tasks_per_run': manifest['max_tasks_per_run'], 'next_tasks': plan}, ensure_ascii=False))
        else:
            print(json.dumps(queue.report(), ensure_ascii=False))
    finally:
        queue.close()


if __name__ == '__main__':
    main()

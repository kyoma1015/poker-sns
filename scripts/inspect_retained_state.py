"""Sanitized read-only continuity observation; never authorizes execution.

This packages the coordinator's existing manual digest algorithm. It is not a
controller, a state repair tool, a scheduler or evidence of automatic startup.
The caller must obtain the expected checkpoint and task manifest from trusted
storage, separately from the database being checked.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys


class InspectionError(ValueError):
    """Public fixed reason only: never include a path or database value."""


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InspectionError('INVALID_INPUT')
        result[key] = value
    return result


def _nonfinite(_value):
    raise InspectionError('INVALID_INPUT')


def _float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise InspectionError('INVALID_INPUT')
    return parsed


def _bytes(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise InspectionError('INVALID_INPUT')
    with path.open('rb') as source:
        raw = source.read(8 * 1024 * 1024 + 1)
    if len(raw) > 8 * 1024 * 1024:
        raise InspectionError('INVALID_INPUT')
    return raw


def _json(path):
    try:
        return json.loads(_bytes(path).decode('utf-8'), object_pairs_hook=_pairs,
                          parse_constant=_nonfinite, parse_float=_float)
    except (OSError, UnicodeError, ValueError, RecursionError):
        raise InspectionError('INVALID_INPUT') from None


def _integer(value):
    return type(value) is int and value >= 0


def _expected(value):
    fields = ('total', 'counts', 'full_rows_digest', 'run_count', 'run_limit',
              'original4', 'checkpoint_sha256')
    if (type(value) is not dict or not all(key in value for key in fields)
            or not _integer(value['total']) or value['total'] > 10000
            or not _integer(value['run_count']) or not _integer(value['run_limit'])
            or type(value['counts']) is not dict
            or any(not isinstance(k, str) or not _integer(v) for k, v in value['counts'].items())
            or sum(value['counts'].values()) != value['total']
            or type(value['original4']) is not list or len(value['original4']) != 4
            or any(not isinstance(value[k], str) or re.fullmatch('[a-f0-9]{64}', value[k]) is None
                   for k in ('full_rows_digest', 'checkpoint_sha256'))):
        raise InspectionError('INVALID_INPUT')
    original = value['original4']
    if (any(type(row) is not dict or set(row) != {'id', 'match', 'status'}
            or not isinstance(row['id'], str) or re.fullmatch('[A-Za-z0-9_-]{1,80}', row['id']) is None
            or row['match'] is not True or not isinstance(row['status'], str)
            or not 1 <= len(row['status']) <= 80 for row in original)
            or len({row['id'] for row in original}) != 4):
        raise InspectionError('INVALID_INPUT')
    return {key: value[key] for key in fields}


def inspect_retained_state(state, manifest, checkpoint, expected):
    """Match trusted expectations using one SQLite read transaction.

    Whole rows are kept only in process memory for hashing. Tokens, evidence,
    SQLite bytes and raw SQL errors are never returned. WAL is read normally;
    immutable=1 is deliberately not used because it can ignore committed WAL.
    """
    expected = _expected(_json(expected))
    manifest = _json(manifest)
    tasks = manifest.get('tasks') if type(manifest) is dict else None
    if (type(tasks) is not list or len(tasks) != 4
            or any(type(t) is not dict or not isinstance(t.get('id'), str)
                   or re.fullmatch('[A-Za-z0-9_-]{1,80}', t['id']) is None for t in tasks)
            or len({t['id'] for t in tasks}) != 4):
        raise InspectionError('INVALID_INPUT')
    try:
        state = Path(state)
        if state.is_symlink() or not state.is_file():
            raise InspectionError('STATE_UNAVAILABLE')
    except (OSError, TypeError, ValueError):
        raise InspectionError('STATE_UNAVAILABLE') from None
    try:
        checkpoint_digest = hashlib.sha256(_bytes(checkpoint)).hexdigest()
    except (OSError, InspectionError):
        raise InspectionError('CHECKPOINT_UNAVAILABLE') from None
    db = None
    try:
        db = sqlite3.connect(state.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        names = [row[1] for row in db.execute('PRAGMA table_info(development_jobs)')]
        if names != ['id', 'lane', 'spec_hash', 'status', 'attempts', 'token', 'expires', 'evidence']:
            raise InspectionError('STATE_UNAVAILABLE')
        rows = db.execute('SELECT * FROM development_jobs ORDER BY id LIMIT 10001').fetchall()
        if len(rows) > 10000:
            raise InspectionError('STATE_UNAVAILABLE')
        original = []
        for task in tasks:
            row = db.execute('SELECT spec_hash,status FROM development_jobs WHERE id=?', (task['id'],)).fetchone()
            match = bool(row and row[0] == hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest())
            original.append({'id': task['id'], 'match': match, 'status': row[1] if row else None})
        limits = db.execute('SELECT run_limit FROM continuation_limits').fetchall()
        if len(limits) != 1:
            raise InspectionError('STATE_UNAVAILABLE')
        observed = {
            'total': len(rows),
            'counts': dict(db.execute('SELECT status,count(*) FROM development_jobs GROUP BY status')),
            'full_rows_digest': hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest(),
            'run_count': db.execute('SELECT count(*) FROM continuation_runs').fetchone()[0],
            'run_limit': limits[0][0], 'original4': original,
            'checkpoint_sha256': checkpoint_digest,
        }
    except (sqlite3.Error, TypeError, UnicodeError, ValueError) as error:
        if isinstance(error, InspectionError):
            raise
        raise InspectionError('STATE_UNAVAILABLE') from None
    finally:
        if db is not None:
            db.close()
    if not all(row['match'] for row in original):
        raise InspectionError('TASK_CONTINUITY_MISMATCH')
    if checkpoint_digest != expected['checkpoint_sha256']:
        raise InspectionError('CHECKPOINT_MISMATCH')
    if observed != expected:
        raise InspectionError('STATE_MISMATCH')
    return observed


class _Parser(argparse.ArgumentParser):
    def error(self, _message):
        raise InspectionError('INVALID_ARGUMENTS')


def main(argv=None):
    try:
        parser = _Parser(description='Read-only retained-state continuity; does not grant execution.')
        for name in ('state', 'manifest', 'checkpoint', 'expected'):
            parser.add_argument('--' + name, required=True)
        args = parser.parse_args(argv)
        observed = inspect_retained_state(args.state, args.manifest, args.checkpoint, args.expected)
        result = {'verdict': 'PASS', 'execution_allowed': False, 'automatic_startup': 'UNKNOWN', 'observed': observed}
        code = 0
    except InspectionError as error:
        result = {'verdict': 'BLOCKED', 'reason': str(error), 'execution_allowed': False, 'automatic_startup': 'UNKNOWN'}
        code = 2
    print(json.dumps(result, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())

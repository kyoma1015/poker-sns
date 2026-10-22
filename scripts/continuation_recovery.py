"""Reviewed continuation planning and bounded host-session recovery.

A host adapter, not a daemon, quota detector or authentication provider. Only the
trusted coordinator may attest review, baseline results and stopped agents.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

from code_worker import Leases, command, protected_hashes, validate_spec
from pr_overlap import verify_overlap_review


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def extract_candidates(sources):
    """Extract suggestions only. Untrusted issue/document text never becomes code."""
    suggestions = []
    for source in sources[:100]:
        if source.get('lane') not in ('A', 'B', 'C', 'D'):
            continue
        for line in str(source.get('text', '')).splitlines()[:1000]:
            match = re.match(r'^\s*[-*]\s+\[ \]\s+(.+)$', line)
            if match:
                suggestions.append({'lane': source['lane'], 'reference': str(source.get('reference', ''))[:300],
                                    'title': match[1][:200], 'status': 'review_required'})
                if len(suggestions) >= 100:
                    return suggestions
    return suggestions


class Continuation:
    def __init__(self, state, anchor):
        """Never create a replacement for missing durable development state.

        Anchor is a coordinator-retained map of existing immutable job IDs to
        spec_hash. It is not a GitHub-exported database or a secret token.
        """
        self.path = Path(state)
        if not self.path.is_file() or self.path.is_symlink() or not anchor:
            raise ValueError('existing durable state and nonempty continuity anchor required')
        probe = sqlite3.connect('file:' + str(self.path.resolve()) + '?mode=ro', uri=True)
        try:
            for ident, expected in anchor.items():
                row = probe.execute('SELECT spec_hash FROM development_jobs WHERE id=?', (ident,)).fetchone()
                if row is None or row[0] != expected:
                    raise ValueError('durable state continuity anchor mismatch')
        except sqlite3.Error:
            raise ValueError('durable lease schema unavailable') from None
        finally:
            probe.close()
        self.leases = Leases(self.path)
        self.db = self.leases.db
        self.db.execute('CREATE TABLE IF NOT EXISTS continuation_runs (id TEXT PRIMARY KEY, started REAL NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS continuation_limits (id INTEGER PRIMARY KEY CHECK(id=1), run_limit INTEGER NOT NULL)')
        self.db.execute('INSERT OR IGNORE INTO continuation_limits VALUES(1,28)')
        self.db.execute('CREATE TABLE IF NOT EXISTS continuation_candidates (id TEXT PRIMARY KEY, spec_hash TEXT NOT NULL)')
        self.db.execute('''CREATE TABLE IF NOT EXISTS continuation_failures (
            id TEXT PRIMARY KEY, kind TEXT NOT NULL, not_before REAL NOT NULL,
            context TEXT NOT NULL, checkpoint TEXT NOT NULL)''')
        self.db.execute('''CREATE TABLE IF NOT EXISTS continuation_discoveries (
            id TEXT PRIMARY KEY, lane TEXT NOT NULL, reference TEXT NOT NULL,
            title TEXT NOT NULL, owner TEXT,
            status TEXT NOT NULL CHECK(status IN ('review_required','blocked','dismissed')))''')

    def close(self):
        self.leases.close()

    def discover(self, sources):
        """Persist bounded suggestions, never reviewed tasks or execution leases."""
        batch = {}
        for suggestion in extract_candidates(sources):
            metadata = {key: suggestion[key] for key in ('lane', 'reference', 'title')}
            batch[digest(metadata)] = metadata
        if not batch:
            return []
        self.db.execute('BEGIN IMMEDIATE')
        try:
            existing = {row[0] for row in self.db.execute('SELECT id FROM continuation_discoveries')}
            if len(existing | batch.keys()) > 1000:
                raise ValueError('discovery capacity exceeded')
            result = []
            for ident, metadata in sorted(batch.items()):
                self.db.execute('''INSERT OR IGNORE INTO continuation_discoveries
                    (id,lane,reference,title,owner,status) VALUES(?,?,?,?,NULL,'review_required')''',
                    (ident, metadata['lane'], metadata['reference'], metadata['title']))
                row = self.db.execute('''SELECT id,lane,reference,title,owner,status
                    FROM continuation_discoveries WHERE id=?''', (ident,)).fetchone()
                result.append(dict(zip(('id','lane','reference','title','owner','status'), row)))
            self.db.execute('COMMIT')
            return result
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def discoveries(self, lane=None):
        """Private review metadata; does not promote suggestions or reveal tokens."""
        if lane is not None and lane not in ('A', 'B', 'C', 'D'):
            raise ValueError('invalid discovery lane')
        query = 'SELECT id,lane,reference,title,owner,status FROM continuation_discoveries'
        rows = self.db.execute(query + (' WHERE lane=?' if lane is not None else '') + ' ORDER BY id',
                               (lane,) if lane is not None else ())
        return [dict(zip(('id','lane','reference','title','owner','status'), row)) for row in rows]

    def set_discovery(self, ident, owner, status):
        """Coordinator assignment only; execution still requires a reviewed descriptor."""
        if (not isinstance(ident, str) or not re.fullmatch(r'[a-f0-9]{64}', ident)
                or status not in ('review_required', 'blocked', 'dismissed')
                or (owner is not None and
                    (not isinstance(owner, str) or not re.fullmatch(r'[A-Za-z0-9_./@-]{1,80}', owner)))):
            raise ValueError('invalid discovery assignment')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            cursor = self.db.execute('UPDATE continuation_discoveries SET owner=?,status=? WHERE id=?',
                                     (owner, status, ident))
            if cursor.rowcount != 1:
                raise ValueError('unknown discovery')
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def restrict_remaining_runs(self, remaining):
        """Import existing scheduler remainder. Never extend/reset its finite cap."""
        if type(remaining) is not int or not 0 <= remaining <= 28:
            raise ValueError('remaining original schedule count must be in 0..28')
        self.db.execute('BEGIN IMMEDIATE')
        try:
            used = self.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0]
            self.db.execute('UPDATE continuation_limits SET run_limit=MIN(run_limit,?) WHERE id=1', (used + remaining,))
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def reserve_run(self, run_id, now=None):
        """Book one finite host invocation. Does not invoke an AI/scheduler."""
        if not isinstance(run_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', run_id):
            raise ValueError('bounded immutable invocation ID required')
        now = time.time() if now is None else now
        self.db.execute('BEGIN IMMEDIATE')
        try:
            used = self.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0]
            limit = self.db.execute('SELECT run_limit FROM continuation_limits WHERE id=1').fetchone()[0]
            existing = self.db.execute('SELECT 1 FROM continuation_runs WHERE id=?', (run_id,)).fetchone()
            if existing or used >= min(28, limit):
                self.db.execute('COMMIT'); return False
            self.db.execute('INSERT INTO continuation_runs VALUES(?,?)', (run_id, now))
            self.db.execute('COMMIT'); return True
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def _candidate(self, candidate, repository):
        task = candidate['task']
        validate_spec({'version': 1, 'repository': 'kyoma1015/poker-sns', 'tasks': [task]})
        if candidate.get('reviewed') is not True or candidate.get('risk') not in ('low', 'medium'):
            raise ValueError('review_and_risk_required')
        for name in ('purpose', 'execution_conditions', 'completion_conditions', 'references'):
            if not candidate.get(name):
                raise ValueError('missing_review_metadata')
        if any(any(char in path for char in '*?[]') for path in task['allowed_paths'] + task['protected_tests']):
            raise ValueError('exact_paths_required')
        if command(['git', 'rev-parse', task['base_sha'] + '^{commit}'], repository) != task['base_sha']:
            raise ValueError('base_missing')
        baseline = candidate.get('baseline', {})
        if (baseline.get('source') != 'trusted_host_verified' or baseline.get('failed') is not True
                or type(baseline.get('test_count')) is not int or baseline['test_count'] < 1
                or baseline.get('base_sha') != task['base_sha'] or baseline.get('test_profile') != task['test_profile']):
            raise ValueError('fixed_failed_baseline_required')
        expected = baseline.get('protected_sha256', {})
        if set(expected) != set(task['protected_tests']):
            raise ValueError('fixed_acceptance_hashes_required')
        for path, sha in expected.items():
            # cat-file reads exact Git bytes rather than mutable working-tree files.
            import subprocess
            proc = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'cat-file', 'blob', task['base_sha'] + ':' + path],
                                  cwd=repository, capture_output=True, timeout=10, check=False)
            if proc.returncode or hashlib.sha256(proc.stdout).hexdigest() != sha:
                raise ValueError('protected_acceptance_mismatch')
        for dependency in candidate.get('dependencies', []):
            row = self.db.execute('SELECT status FROM development_jobs WHERE id=?', (dependency,)).fetchone()
            if row is None or row[0] != 'implemented':
                raise ValueError('dependency_incomplete')
        return task

    def plan(self, candidates, observations, repository, now=None):
        """Return <=4 reviewed descriptors. Still requires host prepare/dispatch/finish.

        Fresh complete PR file/head observations come from the authorized host.
        Reading only titles or CI does not constitute a complete overlap check.
        """
        now = time.time() if now is None else now
        result = {'manifest': {'version': 1, 'repository': 'kyoma1015/poker-sns', 'tasks': []},
                  'blocked': [], 'daemon_running': False}
        stamp = observations.get('checked_at')
        if (observations.get('complete') is not True or not isinstance(stamp, (int, float))
                or not -5 <= now - stamp <= 120 or not isinstance(observations.get('open_prs'), list)):
            result['blocked'].append({'reason': 'fresh_complete_pr_snapshot_required'}); return result
        if not isinstance(candidates, list) or len(candidates) > 100:
            raise ValueError('bounded reviewed candidate catalog required')
        selected = set()
        for candidate in candidates:
            ident = candidate.get('task', {}).get('id', 'unknown')
            try:
                task = self._candidate(candidate, repository)
                hashed = digest(candidate)
                old = self.db.execute('SELECT spec_hash FROM continuation_candidates WHERE id=?', (ident,)).fetchone()
                if old and old[0] != hashed:
                    raise ValueError('immutable_candidate_changed')
                self.db.execute('INSERT OR IGNORE INTO continuation_candidates VALUES(?,?)', (ident, hashed))
                persisted = self.db.execute('SELECT spec_hash FROM continuation_candidates WHERE id=?', (ident,)).fetchone()
                if persisted is None or persisted[0] != hashed:
                    raise ValueError('immutable_candidate_changed')
                existing = self.db.execute('SELECT status FROM development_jobs WHERE id=?', (ident,)).fetchone()
                if existing:
                    raise ValueError('existing_task_requires_reconciliation')
                if self.db.execute("SELECT 1 FROM development_jobs WHERE lane=? AND status='running'", (task['lane'],)).fetchone():
                    raise ValueError('active_lane_lease')
                if task['lane'] in selected:
                    raise ValueError('lane_selected')
                inherited = candidate.get('inherited_prs', {})
                for pr in observations['open_prs']:
                    if not isinstance(pr.get('changed_paths'), list) or not isinstance(pr.get('head'), str):
                        raise ValueError('incomplete_pr_files')
                    if pr['head'] == task['branch']:
                        raise ValueError('existing_branch_pr')
                    if set(pr['changed_paths']) & set(task['allowed_paths']):
                        pin = inherited.get(str(pr['number']))
                        if pin == pr.get('head_sha') and re.fullmatch(r'[0-9a-f]{40}', str(pin)):
                            command(['git', 'merge-base', '--is-ancestor', pin, task['base_sha']], repository)
                        elif str(pr['number']) in candidate.get('overlap_reviews', {}):
                            verify_overlap_review(candidate, pr, repository)
                        else:
                            raise ValueError('overlapping_open_pr')
                selected.add(task['lane']); result['manifest']['tasks'].append(task)
            except (ValueError, KeyError, TypeError, RuntimeError):
                # Reason codes only; candidate instructions, shell output or auth never logged.
                import sys
                error = sys.exc_info()[1]
                reason = str(error)
                if not re.fullmatch(r'[a-z_]{1,80}', reason):
                    reason = 'candidate_validation_failed'
                result['blocked'].append({'id': ident, 'reason': reason})
        return result

    def _checkpoint(self, context):
        task = context['task']; worktree = Path(context['worktree'])
        if command(['git', 'rev-parse', 'HEAD'], worktree) != context['base_sha']:
            raise ValueError('checkpoint HEAD changed')
        if protected_hashes(worktree, task['protected_tests']) != context['before']:
            raise ValueError('protected checkpoint acceptance changed')
        changed = set(command(['git', 'diff', '--name-only', 'HEAD'], worktree).splitlines())
        changed.update(command(['git', 'ls-files', '--others'], worktree).splitlines())
        changed.update(command(['git', 'diff', '--cached', '--name-only'], worktree).splitlines())
        if not changed <= set(task['allowed_paths']):
            raise ValueError('out-of-scope checkpoint changes')
        hashes = {}
        for relative in task['allowed_paths']:
            path = worktree / relative
            if path.is_symlink() or not path.resolve().is_relative_to(worktree.resolve()):
                raise ValueError('unsafe checkpoint source')
            if not path.exists():
                # Missing paths are allowed only when not deleting tracked source.
                if relative in changed:
                    raise ValueError('checkpoint source deletion')
                hashes[relative] = None
            elif not path.is_file():
                raise ValueError('checkpoint source is not a file')
            else:
                hashes[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
        return digest({'head': context['base_sha'], 'protected': context['before'], 'sources': hashes})

    def defer_host(self, task_id, token, kind, *, agent_stopped, now=None, retry_after=300):
        """Coordinator reports witnessed failure AFTER stopping the real agent.

        Never pass raw exception text. Quota/transient get at most one delayed
        retry; auth/permission/runtime/unknown failures require human/runtime fix.
        """
        if agent_stopped is not True:
            raise ValueError('coordinator must stop agent before checkpoint')
        if kind not in ('quota', 'transient', 'authentication', 'permission', 'runtime', 'unknown'):
            raise ValueError('classified failure required')
        if type(retry_after) not in (int, float) or not 1 <= retry_after <= 86400:
            raise ValueError('bounded retry delay required')
        now = time.time() if now is None else now
        self.db.execute('BEGIN IMMEDIATE')
        try:
            row = self.db.execute("SELECT evidence,attempts FROM development_jobs WHERE id=? AND token=? AND status='running' AND expires>?", (task_id, token, now)).fetchone()
            if row is None:
                raise ValueError('missing or expired lease; no automatic stealing')
            context = json.loads(row[0])
            if context.get('prepared_for') != 'host_session':
                raise ValueError('host prepared context required')
            checkpoint = self._checkpoint(context)
            retry = kind in ('quota', 'transient') and row[1] < 2
            self.db.execute('INSERT OR REPLACE INTO continuation_failures VALUES(?,?,?,?,?)',
                            (task_id, kind, now + retry_after, json.dumps(context), checkpoint))
            self.leases.finish(task_id, token, 'retry_wait' if retry else 'blocked',
                               {'failure_class': kind, 'checkpoint_preserved': True, 'retry_eligible': retry}, now=now)
            self.db.execute('COMMIT')
            return {'id': task_id, 'status': 'deferred' if retry else 'blocked', 'failure_class': kind,
                    'retry_after': now + retry_after if retry else None}
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def resume_host(self, task_id, now=None):
        """Return PRIVATE prepared receipt for trusted host dispatch, never publish.

        Existing context/worktree is retained and revalidated. Requires a new
        formal host dispatch; a recovered lease is not real source execution.
        """
        now = time.time() if now is None else now
        row = self.db.execute('SELECT kind,not_before,context,checkpoint FROM continuation_failures WHERE id=?', (task_id,)).fetchone()
        job = self.db.execute('SELECT status,attempts FROM development_jobs WHERE id=?', (task_id,)).fetchone()
        if not row or not job or row[0] not in ('quota', 'transient') or row[1] > now or job[0] != 'retry_wait' or job[1] >= 2:
            return None
        context = json.loads(row[2])
        if self._checkpoint(context) != row[3]:
            raise ValueError('retained worktree changed after stop; review required')
        token = self.leases.claim(context['task'], seconds=360, now=now)
        if token is None:
            return None
        self.db.execute("UPDATE development_jobs SET evidence=? WHERE id=? AND token=? AND status='running'",
                        (json.dumps(context), task_id, token))
        return {'id': task_id, 'status': 'prepared', 'executor': 'host_session',
                'worktree': context['worktree'], 'lease_token': token,
                'real_ai_implementation': False, 'recovered_checkpoint': True}

    def public_checkpoint(self):
        """Token/context-free progress for GitHub. Cannot replace private state."""
        return {'version': 1, 'daemon_running': False, 'run_count': self.db.execute('SELECT COUNT(*) FROM continuation_runs').fetchone()[0],
                'run_limit': self.db.execute('SELECT run_limit FROM continuation_limits WHERE id=1').fetchone()[0],
                'jobs': [dict(zip(('id','lane','status','attempts'), row)) for row in self.db.execute('SELECT id,lane,status,attempts FROM development_jobs ORDER BY id')],
                'failures': [dict(zip(('id','failure_class','retry_at'), row)) for row in self.db.execute('SELECT id,kind,not_before FROM continuation_failures ORDER BY id')]}

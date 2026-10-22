"""Finite, lease-backed Codex code worker. Real executor is opt-in and fail-closed.

No daemon, model API key, production action, merge or deployment is created here.
"""
import argparse
import concurrent.futures
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import signal
import sqlite3
import subprocess
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse
import fcntl
from contextlib import contextmanager

LANES = ('A', 'B', 'C', 'D')
ROOT = Path(__file__).resolve().parents[1]
PROFILES = {
    'queue': [('python', '-B', 'tests/automation/test_development_queue.py')],
    'node': [('node', '--test', 'tests/worker-acceptance.test.mjs')],
    'python': [('python', '-B', '-m', 'unittest', 'discover', '-s', 'tests/worker_acceptance', '-v')],
    'tda': [('node', 'tests/tda-quiz-data.test.mjs')],
    'diagnosis': [('node', 'tests/player-type.test.mjs')],
    'worker': [('python', '-B', 'tests/automation/test_code_worker.py')],
}
DENIED_PARTS = {'.git', '.github', 'node_modules', 'supabase', 'sql', 'handoff'}


def path_ok(value):
    if not isinstance(value, str):
        return False
    path = PurePosixPath(value)
    return (value and not path.is_absolute() and '..' not in path.parts
            and not any(part.lower() in DENIED_PARTS for part in path.parts)
            and not any(part.startswith('.env') for part in path.parts))


def validate_spec(spec):
    if spec.get('version') != 1 or spec.get('repository') != 'kyoma1015/poker-sns':
        raise ValueError('unsupported repository/manifest')
    tasks = spec.get('tasks', [])
    if not isinstance(tasks, list) or not 1 <= len(tasks) <= 4:
        raise ValueError('one to four reviewed tasks required')
    seen = set()
    for task in tasks:
        if task.get('lane') not in LANES or task['lane'] in seen:
            raise ValueError('one task per lane per run')
        seen.add(task['lane'])
        if not re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', task.get('id', '')):
            raise ValueError('invalid immutable task ID')
        if not re.fullmatch(r'[0-9a-f]{40}', task.get('base_sha', '')):
            raise ValueError('full immutable base SHA required')
        if not re.fullmatch(r'codex/[a-zA-Z0-9_/-]{1,100}', task.get('branch', '')) or '..' in task['branch']:
            raise ValueError('dedicated codex branch required')
        if task.get('test_profile') not in PROFILES:
            raise ValueError('test profile is not allowlisted')
        allowed = task.get('allowed_paths', [])
        protected = task.get('protected_tests', [])
        if not allowed or not isinstance(allowed, list) or not all(path_ok(x) for x in allowed):
            raise ValueError('safe exact allowed paths required')
        if not protected or not all(path_ok(x) for x in protected):
            raise ValueError('immutable acceptance tests required')
        if set(allowed) & set(protected):
            raise ValueError('acceptance tests cannot be edited by worker')
        if not isinstance(task.get('instruction'), str) or not 1 <= len(task['instruction']) <= 6000:
            raise ValueError('bounded reviewed instruction required')
        if 'command' in task or 'shell' in task:
            raise ValueError('manifest cannot provide executable commands')
    return spec


def scrub(text):
    text = re.sub(r'(?i)(bearer\s+)[^\s]+', r'\1[REDACTED]', str(text))
    text = re.sub(r'\b(?:sk-[A-Za-z0-9_-]{10,}|gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b', '[REDACTED]', text)
    text = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[REDACTED_JWT]', text)
    return text[:2000]


def child_env(auth=False):
    # Credentials never enter the model's shell environment or test process.
    names = ['PATH', 'LANG', 'LC_ALL', 'TMPDIR', 'SYSTEMROOT']
    if auth:
        names += ['HOME', 'CODEX_HOME', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY',
                  'SSL_CERT_FILE', 'SSL_CERT_DIR', 'REQUESTS_CA_BUNDLE', 'NODE_EXTRA_CA_CERTS']
    result = {key: os.environ[key] for key in names if key in os.environ}
    result['GIT_TERMINAL_PROMPT'] = '0'
    return result


def command(argv, cwd, timeout=60, env=None, include_stderr=False):
    if argv[0] == 'git':
        argv = ['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false', *argv[1:]]
    result = subprocess.run(argv, cwd=cwd, env=env, timeout=timeout, text=True,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError(scrub(f'{argv[0]} exited {result.returncode}: {result.stderr}'))
    return (result.stdout + (result.stderr if include_stderr else "")).strip()


def acceptance_count(output):
    counts = re.findall(r'(?:Ran\s+(\d+)\s+tests?|(?:#|ℹ)\s*tests\s+(\d+))', output)
    return sum(int(left or right) for left, right in counts)


def finite_lease_number(value, label):
    if type(value) not in (int, float):
        raise ValueError('lease ' + label + ' must be a finite number')
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError('lease ' + label + ' must be a finite number')
    return value


class Leases:
    def __init__(self, path):
        with setup_lock(path):
            self.db = sqlite3.connect(path, timeout=10, isolation_level=None)
            try:
                self.db.execute('PRAGMA journal_mode=WAL')
                self.db.execute('PRAGMA busy_timeout=10000')
                self.db.execute('''CREATE TABLE IF NOT EXISTS development_jobs (
                  id TEXT PRIMARY KEY, lane TEXT NOT NULL, spec_hash TEXT NOT NULL,
                  status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0,
                  token TEXT, expires REAL, evidence TEXT)''')
            except BaseException:
                self.db.close()
                raise

    def close(self):
        self.db.close()

    def claim(self, task, seconds=900, now=None):
        now = finite_lease_number(time.time() if now is None else now, 'clock')
        seconds = finite_lease_number(seconds, 'duration')
        if seconds <= 0:
            raise ValueError('lease duration must be positive')
        expires = finite_lease_number(now + seconds, 'expiry')
        digest = hashlib.sha256(json.dumps(task, sort_keys=True).encode()).hexdigest()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            self.db.execute("UPDATE development_jobs SET status='blocked', token=NULL, evidence='lease expired; review required' WHERE status='running' AND expires<=?", (now,))
            old = self.db.execute('SELECT spec_hash,status,attempts FROM development_jobs WHERE id=?', (task['id'],)).fetchone()
            if old and old[0] != digest:
                raise ValueError('immutable task ID cannot change specification')
            active = self.db.execute("SELECT 1 FROM development_jobs WHERE lane=? AND status='running'", (task['lane'],)).fetchone()
            if active or (old and (old[1] != 'retry_wait' or old[2] >= 2)):
                self.db.execute('COMMIT')
                return None
            token = uuid.uuid4().hex
            if old:
                self.db.execute("UPDATE development_jobs SET status='running',attempts=attempts+1,token=?,expires=? WHERE id=?", (token, expires, task['id']))
            else:
                self.db.execute("INSERT INTO development_jobs(id,lane,spec_hash,status,attempts,token,expires) VALUES(?,?,?,'running',1,?,?)", (task['id'], task['lane'], digest, token, expires))
            self.db.execute('COMMIT')
            return token
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def finish(self, task_id, token, status, evidence, now=None):
        if status not in ('implemented', 'blocked', 'failed', 'retry_wait'):
            raise ValueError('invalid terminal status')
        now = finite_lease_number(time.time() if now is None else now, 'clock')
        cursor = self.db.execute("UPDATE development_jobs SET status=?,token=NULL,expires=NULL,evidence=? WHERE id=? AND token=? AND status='running' AND expires>?",
                                 (status, json.dumps(evidence), task_id, token, now))
        if cursor.rowcount != 1:
            raise ValueError('invalid/expired lease; cannot publish completion')

    def report(self):
        rows = self.db.execute('SELECT id,lane,status,attempts,evidence FROM development_jobs ORDER BY rowid').fetchall()
        return [dict(zip(('id', 'lane', 'status', 'attempts', 'evidence'), row)) for row in rows]


def protected_hashes(worktree, paths):
    result = {}
    for relative in paths:
        path = worktree / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError('immutable acceptance file missing or symlinked: ' + relative)
        result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def checked_changes(worktree, allowed):
    changed = command(['git', 'diff', '--name-only', 'HEAD'], worktree).splitlines()
    untracked = command(['git', 'ls-files', '--others'], worktree).splitlines()
    staged = command(['git', 'diff', '--cached', '--name-only'], worktree).splitlines()
    paths = set(changed + untracked + staged)
    if not paths:
        raise ValueError('worker did not change source; not implementation')
    if not paths <= set(allowed):
        raise ValueError('out-of-scope changes: ' + ','.join(sorted(paths - set(allowed))))
    for relative in paths:
        path = worktree / relative
        if path.is_symlink() or not path.exists() or not path.resolve().is_relative_to(worktree.resolve()):
            raise ValueError('symlink/deletion/escape rejected: ' + relative)
    return sorted(paths)


class CodexExecutor:
    name = 'codex_cli'

    def __init__(self, executable, attestation):
        self.executable = str(Path(executable).resolve())
        data = json.loads(Path(attestation).read_text())
        if data != {'auth_mode': 'existing_chatgpt_subscription', 'owner_confirmed': True,
                    'new_paid_services': False}:
            raise ValueError('existing subscription/auth/owner confirmation required; API-key billing unsupported')

    def __call__(self, task, worktree, timeout):
        prompt = ('Implement exactly the reviewed task below. You may edit only these exact paths: '
                  + json.dumps(task['allowed_paths']) + '. Do not edit acceptance tests, git metadata, '
                  'credentials or any other file. Do not commit, push, run network commands, access '
                  'Supabase/production, change billing, or install services. Keep existing specs. '
                  'Make a real source fix; the controller runs immutable acceptance tests and commits.\n'
                  + task['instruction'])
        argv = [self.executable, 'exec', '--ephemeral', '--sandbox', 'workspace-write',
                '-c', 'sandbox_workspace_write.network_access=false',
                '-c', 'shell_environment_policy.inherit="none"',
                '-c', 'shell_environment_policy.include_only=["PATH","TMPDIR","LANG"]',
                '--json', '--color', 'never', '-C', str(worktree), '-']
        # Output is bounded and discarded after extracting non-sensitive event metadata.
        import tempfile
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(argv, cwd=worktree, env=child_env(auth=True), stdin=subprocess.PIPE,
                                       stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                process.stdin.write(prompt.encode())
                process.stdin.close()
                deadline = time.monotonic() + timeout
                while process.poll() is None:
                    if time.monotonic() >= deadline or output.tell() > 2 * 1024 * 1024:
                        os.killpg(process.pid, signal.SIGTERM)
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(process.pid, signal.SIGKILL)
                            process.wait()
                        raise RuntimeError('Codex time/output limit reached')
                    time.sleep(0.1)
                output.seek(0)
                raw = output.read(2 * 1024 * 1024).decode(errors='replace')
                if process.returncode:
                    raise RuntimeError('Codex failed: ' + scrub(raw[-1800:]))
                events = []
                for line in raw.splitlines():
                    try:
                        event = json.loads(line)
                    except ValueError:
                        continue
                    events.append(event.get('type'))
                return {'executor': self.name, 'exit_code': process.returncode,
                        'event_types': sorted(set(str(event) for event in events)), 'output_bytes': len(raw)}
            finally:
                # A terminated leader may leave live descendants in its session.
                # Always clean up the owned process group, even after leader exit.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()


@contextmanager
def setup_lock(state, seconds=30):
    """Serialize state initialization and git preparation across processes."""
    if not math.isfinite(seconds):
        raise ValueError('setup lock timeout must be finite')
    with open(str(state) + '.setup.lock', 'a') as handle:
        deadline = time.monotonic() + seconds
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise RuntimeError('git preparation lock timeout')
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


class GitHubPublisher:
    """Separate opt-in publisher. Credential never reaches Codex or acceptance tests."""
    def __init__(self, token):
        if not token:
            raise ValueError('runtime GitHub credential unavailable; do not register a new secret automatically')
        self.token = token

    def request(self, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode()
        request = urllib.request.Request('https://api.github.com/repos/kyoma1015/poker-sns/' + path,
            data=data, method=method, headers={'Authorization': 'Bearer ' + self.token,
            'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json',
            'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise RuntimeError(f'GitHub {method} refused with HTTP {error.code}; credential not logged') from None

    def publish(self, repository, task, evidence):
        if not evidence.get('real_ai_implementation') or evidence.get('status') != 'implemented_local':
            raise ValueError('test fixtures and blocked tasks cannot publish as real AI implementation')
        branch = task.get('base_branch')
        if not isinstance(branch, str) or not re.fullmatch(r'(main|codex/[A-Za-z0-9_/-]+)', branch):
            raise ValueError('reviewed base branch required for publication')
        base = self.request('GET', 'git/ref/heads/' + urllib.parse.quote(branch, safe=''))
        if base['object']['sha'] != task['base_sha']:
            raise ValueError('remote base advanced; re-review task before publication')
        head = task['branch']
        refs = self.request('GET', 'git/matching-refs/heads/' + urllib.parse.quote(head, safe=''))
        if any(ref['ref'] == 'refs/heads/' + head for ref in refs):
            raise ValueError('remote worker branch exists; never overwrite it')
        # Push uses existing Git transport identity; no token is put on argv or in Git config.
        command(['git', 'push', 'https://github.com/kyoma1015/poker-sns.git',
                 evidence['commit'] + ':refs/heads/' + head], repository, timeout=60)
        pr = self.request('POST', 'pulls', {'base': branch, 'head': head, 'draft': True,
            'title': 'worker(' + task['lane'] + '): ' + task['id'],
            'body': 'Finite real Codex worker implementation. Commit: ' + evidence['commit'] +
                    '\nImmutable acceptance tests passed. No main merge, production DB or deployment.\nChanged paths: ' +
                    ', '.join(evidence['changed_paths']) + '\nCI and required QA remain release gates.'})
        return {'draft_pr': pr['html_url'], 'head': evidence['commit'], 'state': 'draft'}


def validate_and_commit(task, worktree, base, before, evidence):
    if command(['git', 'rev-parse', 'HEAD'], worktree) != base:
        raise ValueError('executor changed git HEAD; publish forbidden')
    paths = checked_changes(worktree, task['allowed_paths'])
    if protected_hashes(worktree, task['protected_tests']) != before:
        raise ValueError('immutable acceptance tests changed')
    evidence['changed_paths'] = paths
    tested_source_hashes = protected_hashes(worktree, paths)
    tested_git_blobs = {path: command(['git', 'hash-object', '--', path], worktree) for path in paths}
    evidence['tested_source_sha256'] = tested_source_hashes
    evidence['tests'] = []
    for argv in PROFILES[task['test_profile']]:
        output = command(list(argv), worktree, timeout=60, env=child_env(), include_stderr=True)
        count = acceptance_count(output)
        if count < 1:
            raise ValueError('acceptance command reported no executed tests')
        evidence['tests'].append({'command': list(argv), 'exit_code': 0,
                                  'test_count': count, 'output_sha256': hashlib.sha256(output.encode()).hexdigest()})
    # Recheck after tests; a test fixture cannot leave unreviewed changes.
    checked_changes(worktree, task['allowed_paths'])
    if protected_hashes(worktree, task['protected_tests']) != before:
        raise ValueError('acceptance test tampering detected after test run')
    if protected_hashes(worktree, paths) != tested_source_hashes:
        raise ValueError('source changed during tests; no tested commit can be produced')
    command(['git', 'diff', '--check'], worktree)
    command(['git', 'add', '--', *paths], worktree)
    for path, blob in tested_git_blobs.items():
        if command(['git', 'rev-parse', ':' + path], worktree) != blob:
            raise ValueError('staged source differs from tested source')
    command(['git', '-c', 'user.name=Poker ID worker', '-c', 'user.email=worker@users.noreply.github.com',
             'commit', '-m', 'worker(' + task['lane'] + '): ' + task['id']], worktree)
    evidence['commit'] = command(['git', 'rev-parse', 'HEAD'], worktree)
    return evidence


def run_task(repository, work_root, state, task, executor, timeout=180):
    leases = Leases(state)
    token = leases.claim(task, seconds=min(1800, timeout + 180))
    if token is None:
        leases.close()
        return {'id': task['id'], 'status': 'skipped_existing_lease_or_result'}
    evidence = {'id': task['id'], 'lane': task['lane'], 'base_sha': task['base_sha'],
                'executor': getattr(executor, 'name', 'test_fixture'), 'production': False,
                'real_ai_implementation': False}
    worktree = Path(work_root) / task['id']
    try:
        if worktree.exists():
            raise ValueError('worktree path already exists; preserve and review before retry')
        base = command(['git', 'rev-parse', task['base_sha'] + '^{commit}'], repository)
        if base != task['base_sha']:
            raise ValueError('immutable source mismatch')
        with setup_lock(state):
            command(['git', 'worktree', 'add', '-b', task['branch'], str(worktree), base], repository)
        before = protected_hashes(worktree, task['protected_tests'])
        evidence['execution'] = executor(task, worktree, timeout)
        validate_and_commit(task, worktree, base, before, evidence)
        evidence['status'] = 'implemented_local'
        evidence['real_ai_implementation'] = getattr(executor, 'name', '') == 'codex_cli'
        evidence['publication'] = 'not_attempted'
        leases.finish(task['id'], token, 'implemented', evidence)
    except Exception as error:
        evidence.update(status='blocked', error=scrub(error))
        # Failed output/worktree retained for review, never reset/deleted automatically.
        try:
            leases.finish(task['id'], token, 'blocked', evidence)
        except ValueError:
            evidence['lease_status'] = 'expired; cannot finalize'
    finally:
        leases.close()
    return evidence


def prepare_host_session(repository, work_root, state, task, now=None):
    """Trusted host coordinator only: acquire lease before collaboration dispatch."""
    validate_spec({'version': 1, 'repository': 'kyoma1015/poker-sns', 'tasks': [task]})
    leases = Leases(state)
    token = leases.claim(task, seconds=1500, now=now)
    if token is None:
        leases.close()
        return {'id': task['id'], 'status': 'skipped_existing_lease_or_result'}
    worktree = Path(work_root).resolve() / task['id']
    try:
        if worktree.exists():
            raise ValueError('worktree already exists; preserve and review')
        base = command(['git', 'rev-parse', task['base_sha'] + '^{commit}'], repository)
        if base != task['base_sha']:
            raise ValueError('source SHA mismatch')
        with setup_lock(state):
            command(['git', 'worktree', 'add', '-b', task['branch'], str(worktree), base], repository)
        context = {'task': task, 'worktree': str(worktree), 'before': protected_hashes(worktree, task['protected_tests']),
                   'base_sha': base, 'prepared_for': 'host_session'}
        leases.db.execute('UPDATE development_jobs SET evidence=? WHERE id=? AND token=?',
                          (json.dumps(context), task['id'], token))
        return {'id': task['id'], 'lane': task['lane'], 'status': 'prepared', 'worktree': str(worktree),
                'lease_token': token, 'executor': 'host_session', 'real_ai_implementation': False,
                'next': 'Trusted coordinator dispatches a formal collaboration agent; never treat preparation as execution.'}
    except Exception as error:
        leases.finish(task['id'], token, 'blocked', {'error': scrub(error)}, now=now)
        raise
    finally:
        leases.close()


def finish_host_session(state, task_id, token, receipt, now=None):
    """Verify host-agent changes and commit. Receipt must come from trusted coordinator.

    This is not an API that cryptographically verifies a collaboration identity.
    Agent output alone is untrusted; the host coordinator owns this invocation.
    """
    if (receipt.get('task_id') != task_id or receipt.get('dispatch_source') != 'collaboration'
            or receipt.get('completed') is not True
            or not re.fullmatch(r'/root/[a-z0-9_/]+', receipt.get('agent_id', ''))):
        raise ValueError('trusted coordinator collaboration receipt required')
    leases = Leases(state)
    current = time.time() if now is None else now
    row = leases.db.execute("SELECT evidence FROM development_jobs WHERE id=? AND token=? AND status='running' AND expires>?", (task_id, token, current)).fetchone()
    if row is None:
        leases.close()
        raise ValueError('host lease missing, expired or replayed')
    context = json.loads(row[0])
    if context.get('prepared_for') != 'host_session':
        leases.close()
        raise ValueError('task was not prepared for host collaboration')
    task = context['task']
    evidence = {'id': task_id, 'lane': task['lane'], 'base_sha': task['base_sha'],
                'executor': 'host_session', 'host_agent_id': receipt['agent_id'],
                'real_ai_implementation': False, 'production': False,
                'receipt_source': 'trusted_host_coordinator', 'daemon_running': False}
    try:
        validate_and_commit(task, Path(context['worktree']), context['base_sha'], context['before'], evidence)
        evidence['status'] = 'implemented_local'
        evidence['real_ai_implementation'] = receipt.get('test_fixture') is not True
        evidence['publication'] = 'not_attempted'
        leases.finish(task_id, token, 'implemented', evidence, now=now)
    except Exception as error:
        evidence.update(status='blocked', error=scrub(error))
        try:
            leases.finish(task_id, token, 'blocked', evidence, now=now)
        except ValueError:
            evidence['lease_status'] = 'expired; cannot finalize'
    finally:
        leases.close()
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--repository', type=Path, required=True)
    parser.add_argument('--work-root', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--codex', default='/opt/codex/bin/codex')
    parser.add_argument('--auth-attestation', type=Path)
    parser.add_argument('--enable-code-writing', action='store_true')
    parser.add_argument('--publish-draft', action='store_true')
    args = parser.parse_args()
    spec = validate_spec(json.loads(args.manifest.read_text()))
    if not args.enable_code_writing or args.auth_attestation is None:
        parser.error('real code writing is opt-in and requires verified existing-subscription attestation')
    executor = CodexExecutor(args.codex, args.auth_attestation)
    args.work_root.mkdir(parents=True, exist_ok=True)
    # A finite batch only; process timeout per task and at most four threads.
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(run_task, args.repository.resolve(), args.work_root.resolve(), args.state.resolve(), task, executor)
                   for task in spec['tasks']]
        results = [future.result() for future in futures]
    if args.publish_draft:
        publisher = GitHubPublisher(os.environ.get('GITHUB_TOKEN'))
        for task, result in zip(spec['tasks'], results):
            if result.get('status') == 'implemented_local':
                try:
                    result['publication'] = publisher.publish(args.repository, task, result)
                except Exception as error:
                    result['publication'] = {'status': 'blocked', 'error': scrub(error)}
    report = {'finite_batch': True, 'new_paid_services': False, 'daemon_running': False,
              'real_ai_implementations': sum(result.get('real_ai_implementation', False) for result in results),
              'tasks': results}
    args.output.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0 if all(result.get('status') == 'implemented_local' for result in results) else 2


if __name__ == '__main__':
    raise SystemExit(main())

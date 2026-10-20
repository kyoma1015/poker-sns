import concurrent.futures
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('code_worker', ROOT / 'scripts/code_worker.py')
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)


def git(root, *args):
    return subprocess.check_output(['git', '-c', 'user.name=Worker test', '-c', 'user.email=test@users.noreply.github.com', *args], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()


class FixtureExecutor:
    name = 'test_fixture'

    def __call__(self, task, worktree, timeout):
        (worktree / 'src/value.py').write_text('VALUE = 2\n')
        return {'executor': self.name, 'fixture_only': True}


class CodeWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repository'
        self.repo.mkdir()
        git(self.repo, 'init', '-b', 'main')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/value.py').write_text('VALUE = 1\n')
        (self.repo / 'tests/worker_acceptance').mkdir(parents=True)
        (self.repo / 'tests/worker_acceptance/test_value.py').write_text('import unittest\nfrom src.value import VALUE\nclass ValueTest(unittest.TestCase):\n def test_value(self): self.assertEqual(VALUE, 2)\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'baseline')
        self.sha = git(self.repo, 'rev-parse', 'HEAD')
        self.state = self.root / 'state.sqlite'
        self.work = self.root / 'worktrees'
        self.work.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def task(self, lane='A'):
        return {'id': 'fixture-' + lane, 'lane': lane, 'base_sha': self.sha,
                'base_branch': 'main', 'branch': 'codex/fixture-' + lane,
                'instruction': 'Change the incorrect value to 2.', 'allowed_paths': ['src/value.py'],
                'protected_tests': ['tests/worker_acceptance/test_value.py'], 'test_profile': 'python'}

    def test_four_real_git_worktrees_and_commits_without_faking_ai(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda lane: worker.run_task(self.repo, self.work, self.state, self.task(lane), FixtureExecutor()), worker.LANES))
        self.assertEqual([r['status'] for r in results], ['implemented_local'] * 4)
        self.assertEqual(len({r['commit'] for r in results}), 4)
        self.assertTrue(all(r['real_ai_implementation'] is False for r in results))
        self.assertEqual(git(self.repo, 'rev-parse', 'main'), self.sha)
        self.assertEqual((self.repo / 'src/value.py').read_text(), 'VALUE = 1\n')
        for result in results:
            self.assertEqual(result['changed_paths'], ['src/value.py'])
            self.assertEqual(result['tests'][0]['exit_code'], 0)
        lease = worker.Leases(self.state)
        try:
            self.assertEqual(len(lease.report()), 4)
            self.assertIsNone(lease.claim(self.task('A')))
        finally:
            lease.close()

    def test_two_connections_cannot_claim_same_lane(self):
        first = worker.Leases(self.state)
        second = worker.Leases(self.state)
        try:
            token = first.claim(self.task(), now=100)
            self.assertIsNotNone(token)
            other = self.task(); other['id'] = 'different-A'
            self.assertIsNone(second.claim(other, now=101))
            self.assertIsNotNone(second.claim(self.task('B'), now=101))
        finally:
            first.close(); second.close()

    def test_expired_lease_blocks_and_never_stolen(self):
        leases = worker.Leases(self.state)
        try:
            token = leases.claim(self.task(), seconds=30, now=100)
            self.assertIsNone(leases.claim(self.task(), now=130))
            with self.assertRaises(ValueError):
                leases.finish(self.task()['id'], token, 'implemented', {}, now=130)
            self.assertEqual(leases.report()[0]['status'], 'blocked')
        finally:
            leases.close()

    def test_retry_is_bounded_at_two_attempts(self):
        leases = worker.Leases(self.state)
        try:
            for count in range(2):
                token = leases.claim(self.task(), now=100 + count)
                self.assertIsNotNone(token)
                leases.finish(self.task()['id'], token, 'retry_wait', {}, now=100 + count + .1)
            self.assertIsNone(leases.claim(self.task(), now=200))
        finally:
            leases.close()

    def test_completed_lane_can_claim_the_next_reviewed_task(self):
        leases = worker.Leases(self.state)
        try:
            first = self.task()
            token = leases.claim(first, now=100)
            leases.finish(first['id'], token, 'implemented', {'fixture_only': True}, now=101)
            second = self.task(); second['id'] = 'next-reviewed-A'; second['branch'] = 'codex/next-reviewed-A'
            self.assertIsNotNone(leases.claim(second, now=102))
            self.assertEqual([row['status'] for row in leases.report()], ['implemented', 'running'])
        finally:
            leases.close()

    def test_changed_task_cannot_reuse_immutable_id(self):
        leases = worker.Leases(self.state)
        try:
            leases.claim(self.task(), now=100)
            changed = self.task(); changed['instruction'] = 'different'
            with self.assertRaises(ValueError):
                leases.claim(changed, now=101)
        finally:
            leases.close()

    def test_noop_is_not_implementation(self):
        result = worker.run_task(self.repo, self.work, self.state, self.task(), lambda *args: {})
        self.assertEqual(result['status'], 'blocked')
        self.assertNotIn('commit', result)

    def test_out_of_scope_change_fails_before_commit(self):
        def executor(task, worktree, timeout):
            (worktree / 'src/value.py').write_text('VALUE = 2\n')
            (worktree / 'unreviewed.txt').write_text('not allowed')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), executor)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('out-of-scope', result['error'])

    def test_ignored_secret_file_is_detected(self):
        def executor(task, worktree, timeout):
            (worktree / 'src/value.py').write_text('VALUE = 2\n')
            (worktree / '.env.local').write_text('fixture-only')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), executor)
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('.env.local', result['error'])

    def test_acceptance_tamper_fails(self):
        def executor(task, worktree, timeout):
            (worktree / 'src/value.py').write_text('VALUE = 2\n')
            (worktree / 'tests/worker_acceptance/test_value.py').write_text('')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), executor)
        self.assertEqual(result['status'], 'blocked')
        self.assertNotIn('commit', result)

    def test_failed_acceptance_cannot_commit(self):
        def executor(task, worktree, timeout):
            (worktree / 'src/value.py').write_text('VALUE = 9\n')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), executor)
        self.assertEqual(result['status'], 'blocked')
        self.assertNotIn('commit', result)

    def test_source_symlink_rejected(self):
        def executor(task, worktree, timeout):
            path = worktree / 'src/value.py'; path.unlink(); path.symlink_to('/tmp/nonexistent-worker-target')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), executor)
        self.assertEqual(result['status'], 'blocked')

    def test_existing_worktree_is_preserved(self):
        path = self.work / self.task()['id']; path.mkdir(); (path / 'original').write_text('keep')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), FixtureExecutor())
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual((path / 'original').read_text(), 'keep')

    def test_manifest_rejects_main_shell_secret_paths_and_tampering(self):
        for key, value in [('branch', 'main'), ('base_sha', 'short'), ('test_profile', 'curl'),
                           ('allowed_paths', ['../escape']), ('allowed_paths', ['.env.local']),
                           ('allowed_paths', ['sql/production.sql']), ('allowed_paths', ['tests/worker_acceptance/test_value.py'])]:
            task = self.task(); task[key] = value
            with self.assertRaises(ValueError):
                worker.validate_spec({'version': 1, 'repository': 'kyoma1015/poker-sns', 'tasks': [task]})
        task = self.task(); task['shell'] = 'ignored but rejected'
        with self.assertRaises(ValueError):
            worker.validate_spec({'version': 1, 'repository': 'kyoma1015/poker-sns', 'tasks': [task]})

    def test_acceptance_cannot_mutate_source_then_commit_untested_bytes(self):
        acceptance = self.repo / 'tests/worker_acceptance/test_value.py'
        acceptance.write_text('import unittest\nfrom pathlib import Path\nfrom src.value import VALUE\nclass ValueTest(unittest.TestCase):\n def test_value(self):\n  self.assertEqual(VALUE, 2)\n  Path("src/value.py").write_text("VALUE = 999\\n")\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'mutating acceptance fixture')
        self.sha = git(self.repo, 'rev-parse', 'HEAD')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), FixtureExecutor())
        self.assertEqual(result['status'], 'blocked')
        self.assertIn('source changed during tests', result['error'])
        self.assertNotIn('commit', result)

    def test_wrong_or_replayed_lease_cannot_finish(self):
        leases = worker.Leases(self.state)
        try:
            token = leases.claim(self.task(), now=100)
            with self.assertRaises(ValueError):
                leases.finish(self.task()['id'], 'wrong', 'implemented', {}, now=101)
            leases.finish(self.task()['id'], token, 'implemented', {}, now=101)
            with self.assertRaises(ValueError):
                leases.finish(self.task()['id'], token, 'implemented', {}, now=102)
            self.assertIsNone(leases.claim(self.task(), now=103))
        finally:
            leases.close()

    def test_host_prepare_dispatch_finish_uses_same_acceptance_and_leases(self):
        prepared = worker.prepare_host_session(self.repo, self.work, self.state, self.task(), now=100)
        self.assertEqual(prepared['status'], 'prepared')
        self.assertFalse(prepared['real_ai_implementation'])
        FixtureExecutor()(self.task(), Path(prepared['worktree']), 60)
        receipt = {'task_id': self.task()['id'], 'dispatch_source': 'collaboration', 'completed': True,
                   'agent_id': '/root/test_fixture', 'test_fixture': True}
        result = worker.finish_host_session(self.state, self.task()['id'], prepared['lease_token'], receipt, now=101)
        self.assertEqual(result['status'], 'implemented_local')
        self.assertEqual(result['executor'], 'host_session')
        self.assertFalse(result['real_ai_implementation'])
        self.assertEqual(result['tests'][0]['test_count'], 1)
        with self.assertRaises(ValueError):
            worker.finish_host_session(self.state, self.task()['id'], prepared['lease_token'], receipt, now=102)

    def test_host_missing_receipt_cannot_forge_completion(self):
        prepared = worker.prepare_host_session(self.repo, self.work, self.state, self.task(), now=100)
        with self.assertRaises(ValueError):
            worker.finish_host_session(self.state, self.task()['id'], prepared['lease_token'], {}, now=101)
        self.assertEqual(git(Path(prepared['worktree']), 'rev-parse', 'HEAD'), self.sha)

    def test_zero_test_acceptance_does_not_pass(self):
        acceptance = self.repo / 'tests/worker_acceptance/test_value.py'
        acceptance.write_text('import unittest\n')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-m', 'zero test fixture')
        self.sha = git(self.repo, 'rev-parse', 'HEAD')
        result = worker.run_task(self.repo, self.work, self.state, self.task(), FixtureExecutor())
        self.assertEqual(result['status'], 'blocked')
        self.assertRegex(result['error'], r'no executed tests|Ran 0 tests')

    def test_api_billing_attestation_rejected_without_running_cli(self):
        auth = self.root / 'attestation.json'
        auth.write_text(json.dumps({'auth_mode': 'api_key', 'owner_confirmed': True, 'new_paid_services': False}))
        with self.assertRaises(ValueError):
            worker.CodexExecutor('/not/started', auth)

    def test_fake_executor_cannot_publish_as_real_ai(self):
        publisher = worker.GitHubPublisher('fixture-unused')
        with self.assertRaises(ValueError):
            publisher.publish(self.repo, self.task(), {'status': 'implemented_local', 'real_ai_implementation': False})

    def test_secrets_are_not_in_shell_or_test_environment(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'fixture-secret', 'GITHUB_TOKEN': 'fixture-secret', 'SUPABASE_SERVICE_ROLE_KEY': 'fixture-secret'}):
            for auth in (False, True):
                env = worker.child_env(auth)
                self.assertNotIn('OPENAI_API_KEY', env)
                self.assertNotIn('GITHUB_TOKEN', env)
                self.assertNotIn('SUPABASE_SERVICE_ROLE_KEY', env)
        self.assertNotIn('ghp_testsecret1234', worker.scrub('Bearer ghp_testsecret1234'))


if __name__ == '__main__':
    unittest.main(verbosity=2)

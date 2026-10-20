import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('development_queue', ROOT / 'scripts/development_queue.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def manifest():
    return json.loads((ROOT / '.github/queues/development.json').read_text())


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'queue.sqlite'
        self.q = module.Queue(self.path, manifest())

    def tearDown(self):
        self.q.close()
        self.temp.cleanup()

    def test_four_lanes_are_independent(self):
        leases = [self.q.claim(lane, 100) for lane in module.LANES]
        self.assertEqual(len({x['id'] for x in leases}), 4)

    def test_second_connection_cannot_duplicate_lane(self):
        lease = self.q.claim('A', 100)
        second = module.Queue(self.path, manifest())
        try:
            self.assertIsNone(second.claim('A', 101))
            self.assertIsNotNone(second.claim('B', 101))
        finally:
            second.close()
        self.assertIsNotNone(lease)

    def test_development_tasks_never_execute(self):
        lease = self.q.claim('C', 100)
        self.assertEqual(lease['id'], 'C-queue-validation-20261020')
        self.assertFalse(self.q.report()['autonomous_development_running'])

    def test_success_advances_only_validation_task(self):
        lease = self.q.claim('A', 100)
        self.assertEqual(self.q.finish(lease['id'], lease['token'], True, 'test-log', 101), 'succeeded')
        self.assertIsNone(self.q.claim('A', 102))
        self.assertEqual(self.q.report()['tasks'][0]['status'], 'queued')

    def test_wrong_token_and_empty_evidence_rejected(self):
        lease = self.q.claim('A', 100)
        with self.assertRaises(ValueError):
            self.q.finish(lease['id'], 'wrong', True, 'test-log', 101)
        with self.assertRaises(ValueError):
            self.q.finish(lease['id'], lease['token'], True, '', 101)
        self.assertIsNone(self.q.claim('A', 102))

    def test_expiry_blocks_without_duplicate_retry(self):
        lease = self.q.claim('A', 100)
        self.assertIsNone(self.q.claim('A', lease['expires']))
        row = next(x for x in self.q.report()['tasks'] if x['id'] == lease['id'])
        self.assertEqual(row['status'], 'blocked')
        with self.assertRaises(ValueError):
            self.q.finish(lease['id'], lease['token'], True, 'late', lease['expires'])

    def test_three_attempts_then_terminal_failure(self):
        now = 100
        for attempt in range(3):
            lease = self.q.claim('A', now)
            status = self.q.finish(lease['id'], lease['token'], False, 'failure-log', now + 1)
            self.assertIsNone(self.q.claim('A', now + 2))
            now += 61 * 2 ** attempt
        self.assertEqual(status, 'failed')
        self.assertIsNone(self.q.claim('A', 10000))
        self.assertIsNotNone(self.q.claim('B', 10000))

    def test_reopen_preserves_completed_state(self):
        lease = self.q.claim('A', 100)
        self.q.finish(lease['id'], lease['token'], True, 'test-log', 101)
        second = module.Queue(self.path, manifest())
        try:
            self.assertIsNone(second.claim('A', 102))
        finally:
            second.close()

    def test_manifest_change_cannot_reuse_completed_id(self):
        changed = manifest()
        changed['tasks'][0]['acceptance'] += ' changed'
        with self.assertRaises(ValueError):
            module.Queue(self.path, changed)

    def test_rejects_unbounded_or_executable_configuration(self):
        for field, value in [('max_attempts', 4), ('max_tasks_per_run', 5), ('lease_seconds', 3601), ('code_worker_configured', True), ('mode', 'autonomous')]:
            changed = manifest()
            changed[field] = value
            with self.assertRaises(ValueError):
                module.validate_manifest(changed)
        changed = manifest()
        changed['tasks'][0]['shell'] = 'anything'
        with self.assertRaises(ValueError):
            module.validate_manifest(changed)

    def test_removed_tasks_cannot_run_from_old_state(self):
        changed = manifest()
        changed['tasks'] = [task for task in changed['tasks'] if task['lane'] != 'A']
        second = module.Queue(self.path, changed)
        try:
            self.assertIsNone(second.claim('A', 100))
            self.assertIsNotNone(second.claim('B', 100))
        finally:
            second.close()

    def test_invalid_lane_rejected(self):
        with self.assertRaises(ValueError):
            self.q.claim('production', 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)

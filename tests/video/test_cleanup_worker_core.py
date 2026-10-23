import unittest
from tests.video.cleanup_worker_core import CleanupJob, process_cleanup

JOB = CleanupJob("10000000-0000-0000-0000-000000000001", "path.mp4", "version-1")

class CleanupWorkerTests(unittest.TestCase):
    def run_case(self, post=None, version="version-1", deleted=True):
        calls = []
        result = process_cleanup(
            JOB,
            find_post=lambda *args: post,
            get_object_version=lambda *args: version,
            delete_if_version=lambda *args: calls.append("delete") or deleted,
            mark_complete=lambda *args: calls.append("complete"),
            reschedule=lambda *args: calls.append("retry"),
        )
        return result, calls

    def test_committed_post_retained(self):
        self.assertEqual(self.run_case(post="post-id"), ("RETAINED", ["complete"]))

    def test_object_changed_never_deleted(self):
        self.assertEqual(self.run_case(version="version-2"), ("RETRY", ["retry"]))

    def test_conditional_delete_unsupported_never_completes(self):
        self.assertEqual(self.run_case(deleted=False), ("RETRY", ["delete", "retry"]))

    def test_missing_object_is_complete(self):
        self.assertEqual(self.run_case(version=None), ("ABSENT", ["complete"]))

    def test_conditional_delete_success(self):
        self.assertEqual(self.run_case(), ("DELETED", ["delete", "complete"]))

if __name__ == "__main__":
    unittest.main()

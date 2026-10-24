import unittest
from tests.video.cleanup_worker_core import CleanupJob, process_cleanup

JOB = CleanupJob("10000000-0000-0000-0000-000000000001", "10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4", "version-1")

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

    def test_cross_owner_object_key_never_reaches_delete(self):
        calls = []
        bad = CleanupJob(JOB.owner_id, "20000000-0000-0000-0000-000000000002/30000000-0000-0000-0000-000000000001.mp4", "version-1")
        result = process_cleanup(bad, find_post=lambda *a: calls.append("lookup"),
                                 get_object_version=lambda *a: calls.append("read"),
                                 delete_if_version=lambda *a: calls.append("delete"),
                                 mark_complete=lambda *a: calls.append("complete"),
                                 reschedule=lambda *a: calls.append("retry"))
        self.assertEqual((result, calls), ("RETRY", ["retry"]))

    def test_invalid_extension_never_reaches_delete(self):
        calls = []
        bad = CleanupJob(JOB.owner_id, JOB.owner_id + "/30000000-0000-0000-0000-000000000001.txt", "version-1")
        result = process_cleanup(bad, find_post=lambda *a: calls.append("lookup"),
                                 get_object_version=lambda *a: calls.append("read"),
                                 delete_if_version=lambda *a: calls.append("delete"),
                                 mark_complete=lambda *a: calls.append("complete"),
                                 reschedule=lambda *a: calls.append("retry"))
        self.assertEqual((result, calls), ("RETRY", ["retry"]))

if __name__ == "__main__":
    unittest.main()

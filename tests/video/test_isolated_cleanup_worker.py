import unittest
from unittest.mock import patch
from tests.video.isolated_cleanup_worker import run_one

URL = "http://127.0.0.1:56321"
OWNER = "10000000-0000-0000-0000-000000000001"
PATH = OWNER + "/30000000-0000-0000-0000-000000000001.mp4"

class CleanupWorkerTests(unittest.TestCase):
    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_remote_worker_rejected_before_any_rpc_or_storage(self, rpc):
        for url in ("https://example.supabase.co", "http://localhost:56321",
                    "http://127.0.0.1:56321/"):
            with self.subTest(url=url):
                with self.assertRaises(PermissionError):
                    run_one(url, "isolated", lambda *_: self.fail("inspected"),
                            lambda *_: self.fail("deleted"))
        with self.assertRaises(PermissionError):
            run_one(URL, "", lambda *_: self.fail("inspected"),
                    lambda *_: self.fail("deleted"))
        rpc.assert_not_called()

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_missing_storage_adapters_rejected_before_claim(self, rpc):
        for inspector, deleter in ((None, lambda *_: True),
                                   (lambda *_: "v1", None),
                                   (None, None)):
            with self.subTest(inspector=inspector, deleter=deleter):
                with self.assertRaises(PermissionError):
                    run_one(URL, "isolated", inspector, deleter)
        rpc.assert_not_called()

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_unpinned_object_is_never_deleted(self, rpc):
        rpc.side_effect = [[{"id": 1, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": None}], None, True]
        deleted = []
        outcome = run_one(URL, "isolated", lambda *_: "v1",
                          lambda *args: deleted.append(args))
        self.assertEqual(outcome, "retry")
        self.assertFalse(deleted)
        self.assertFalse(rpc.call_args.args[3]["p_success"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_posted_object_is_retained(self, rpc):
        rpc.side_effect = [[{"id": 1, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], "post-id", True]
        deleted = []
        self.assertEqual(run_one(URL, "isolated", lambda *_: "v1",
                         lambda *args: deleted.append(args)), "complete")
        self.assertFalse(deleted)

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_matching_version_without_atomic_delete_stays_queued(self, rpc):
        rpc.side_effect = [[{"id": 2, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        inspected = []
        deletion_attempts = []
        outcome = run_one(
            URL, "isolated",
            lambda *args: inspected.append(args) or "v1",
            lambda *args: deletion_attempts.append(args) or False)
        self.assertEqual(outcome, "retry")
        self.assertEqual(inspected, [(OWNER, PATH)])
        self.assertEqual(deletion_attempts, [(OWNER, PATH, "v1")])
        self.assertEqual(rpc.call_args.args[2], "video_qa_finish_cleanup")
        self.assertFalse(rpc.call_args.args[3]["p_success"])
        self.assertIn("unsupported", rpc.call_args.args[3]["p_reason"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_atomic_delete_exception_keeps_job_for_retry(self, rpc):
        rpc.side_effect = [[{"id": 3, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        def unavailable(*_):
            raise RuntimeError("atomic delete unavailable")
        self.assertEqual(run_one(URL, "isolated", lambda *_: "v1", unavailable),
                         "retry")
        self.assertFalse(rpc.call_args.args[3]["p_success"])
        self.assertEqual(rpc.call_args.args[3]["p_reason"],
                         "worker operation failed; retry")

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_changed_object_is_retained(self, rpc):
        rpc.side_effect = [[{"id": 1, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        deleted = []
        self.assertEqual(run_one(URL, "isolated", lambda *_: "v2",
                         lambda *args: deleted.append(args)), "retry")
        self.assertFalse(deleted)

if __name__ == "__main__":
    unittest.main()

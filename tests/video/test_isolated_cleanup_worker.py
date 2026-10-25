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
    def test_pinned_absent_object_retries_without_tombstone(self, rpc):
        rpc.side_effect = [[{"id": 4, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        deleted = []
        outcome = run_one(URL, "isolated", lambda *_: None,
                          lambda *args: deleted.append(args))
        self.assertEqual(outcome, "retry")
        self.assertEqual(deleted, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])
        self.assertIn("tombstone", rpc.call_args.args[3]["p_reason"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_invalid_queued_path_never_reaches_storage(self, rpc):
        rpc.side_effect = [[{"id": 5, "owner_id": OWNER,
                             "object_path": OWNER + "/../foreign.mp4",
                             "expected_object_version": "v1"}], True]
        touched = []
        outcome = run_one(URL, "isolated",
                          lambda *args: touched.append(args),
                          lambda *args: touched.append(args))
        self.assertEqual(outcome, "retry")
        self.assertEqual(touched, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_lost_cleanup_lease_does_not_report_completion(self, rpc):
        rpc.side_effect = [[{"id": 6, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], "post-id", False]
        with self.assertRaisesRegex(RuntimeError, "lease lost"):
            run_one(URL, "isolated", lambda *_: "v1",
                    lambda *_: self.fail("posted video deleted"))

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_inspection_error_never_invokes_delete(self, rpc):
        rpc.side_effect = [[{"id": 7, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        def inspection_failed(*_):
            raise TimeoutError("Storage metadata unavailable")
        deleted = []
        self.assertEqual(
            run_one(URL, "isolated", inspection_failed,
                    lambda *args: deleted.append(args)), "retry")
        self.assertEqual(deleted, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_reconciliation_error_never_invokes_storage(self, rpc):
        rpc.side_effect = [[{"id": 8, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}],
                           TimeoutError("PostgREST unavailable"), True]
        touched = []
        self.assertEqual(
            run_one(URL, "isolated",
                    lambda *args: touched.append(args),
                    lambda *args: touched.append(args)), "retry")
        self.assertEqual(touched, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_empty_queue_does_not_touch_storage_or_finish(self, rpc):
        rpc.return_value = []
        touched = []
        self.assertEqual(
            run_one(URL, "isolated",
                    lambda *args: touched.append(args),
                    lambda *args: touched.append(args)), "idle")
        self.assertEqual(touched, [])
        self.assertEqual(rpc.call_count, 1)
        self.assertEqual(rpc.call_args.args[2], "video_qa_claim_cleanup")

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_reconcile_returns_false_and_unpinned_never_inspects(self, rpc):
        rpc.side_effect = [[{"id": 9, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": ""}], None, True]
        touched = []
        self.assertEqual(
            run_one(URL, "isolated",
                    lambda *args: touched.append(args),
                    lambda *args: touched.append(args)), "retry")
        self.assertEqual(touched, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_changed_object_is_retained(self, rpc):
        rpc.side_effect = [[{"id": 1, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "v1"}], None, True]
        deleted = []
        self.assertEqual(run_one(URL, "isolated", lambda *_: "v2",
                         lambda *args: deleted.append(args)), "retry")
        self.assertFalse(deleted)

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_conditional_delete_success_only_for_exact_pinned_version(self, rpc):
        rpc.side_effect = [[{"id": 10, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "generation-10"}], None, True]
        calls = []
        def fenced_delete(owner, path, generation):
            calls.append((owner, path, generation))
            return generation == "generation-10"
        outcome = run_one(URL, "isolated",
                          lambda *_: "generation-10", fenced_delete)
        self.assertEqual(outcome, "complete")
        self.assertEqual(calls, [(OWNER, PATH, "generation-10")])
        self.assertTrue(rpc.call_args.args[3]["p_success"])
        self.assertEqual(rpc.call_args.args[3]["p_reason"], "conditional deletion succeeded")

    @patch("tests.video.isolated_cleanup_worker._rpc")
    def test_aba_replacement_blocks_conditional_delete(self, rpc):
        rpc.side_effect = [[{"id": 11, "owner_id": OWNER, "object_path": PATH,
                             "expected_object_version": "generation-old"}], None, True]
        deletes = []
        outcome = run_one(URL, "isolated", lambda *_: "generation-new",
                          lambda *args: deletes.append(args) or True)
        self.assertEqual(outcome, "retry")
        self.assertEqual(deletes, [])
        self.assertFalse(rpc.call_args.args[3]["p_success"])
        self.assertIn("version changed", rpc.call_args.args[3]["p_reason"])

if __name__ == "__main__":
    unittest.main()

import unittest
from unittest.mock import patch
from contextlib import contextmanager
from tests.video.finalize_boundary import ServerAdapters, finalize_authenticated
from tests.video.finalize_core import PostCommitUnknown

USER = "10000000-0000-0000-0000-000000000001"
PATH = USER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        @contextmanager
        def download(user, path):
            self.calls.append("download")
            try:
                yield "/tmp/test.mp4"
            finally:
                self.calls.append("temp-cleanup")
        self.adapters = ServerAdapters(
            authenticate_token=lambda token: USER if token == "verified" else (_ for _ in ()).throw(PermissionError()),
            verify_owner=lambda user, path: self.calls.append("owner") or (user == USER and path == PATH),
            download_staged=download,
            create_post=lambda user, path, content: self.calls.append("post") or POST,
            delete_staged=lambda path: self.calls.append("delete"),
            reconcile_post=lambda user, path: None,
            enqueue_cleanup=lambda user, path: self.calls.append("queue"),
        )
        self.body = {"object_path": PATH, "content": "hello"}

    def test_isolated_composition_rejects_remote_project_before_adapters(self):
        from tests.video.isolated_composition import build_isolated_adapters
        for project in ("https://example.supabase.co",
                        "http://localhost:56321",
                        "http://127.0.0.1:56321/"):
            with self.subTest(project=project):
                with self.assertRaises(PermissionError):
                    build_isolated_adapters(project_url=project, anon_key="anon",
                                            service_key="service", access_token="jwt")
        for missing in ("anon_key", "service_key", "access_token"):
            with self.subTest(missing=missing):
                kwargs = dict(project_url="http://127.0.0.1:56321",
                              anon_key="anon", service_key="service", access_token="jwt")
                kwargs[missing] = ""
                with self.assertRaises(PermissionError):
                    build_isolated_adapters(**kwargs)

    def test_no_bearer_rejected_before_storage(self):
        with self.assertRaises(PermissionError):
            finalize_authenticated("", self.body, self.adapters)
        self.assertEqual(self.calls, [])

    def test_noncanonical_verified_user_rejected_before_storage(self):
        from dataclasses import replace
        for bad_user in ("A0000000-0000-0000-0000-000000000001", USER.replace("-", "")):
            with self.subTest(bad_user=bad_user):
                self.calls.clear()
                adapters = replace(self.adapters, authenticate_token=lambda token, value=bad_user: value)
                with self.assertRaises(PermissionError):
                    finalize_authenticated("Bearer verified", self.body, adapters)
                self.assertEqual(self.calls, [])

    def test_body_user_id_rejected(self):
        with self.assertRaises(ValueError):
            finalize_authenticated("Bearer verified", {**self.body, "user_id": USER}, self.adapters)
        self.assertEqual(self.calls, [])

    def test_cross_owner_path_rejected(self):
        with self.assertRaises(PermissionError):
            finalize_authenticated("Bearer verified", {**self.body, "object_path": "20000000-0000-0000-0000-000000000002/x.mp4"}, self.adapters)
        self.assertEqual(self.calls, [])

    @patch("tests.video.finalize_core.verify", return_value={"duration": 2})
    def test_success(self, verify):
        self.assertEqual(finalize_authenticated("Bearer verified", self.body, self.adapters), {"post_id": POST})
        self.assertEqual(self.calls, ["owner", "download", "owner", "post", "temp-cleanup"])

    @patch("tests.video.finalize_core.verify", return_value={"duration": 2})
    def test_unknown_commit_never_deletes(self, verify):
        from dataclasses import replace
        adapters = replace(self.adapters, create_post=lambda *args: (_ for _ in ()).throw(PostCommitUnknown()))
        with self.assertRaises(PostCommitUnknown):
            finalize_authenticated("Bearer verified", self.body, adapters)
        self.assertNotIn("delete", self.calls)
        self.assertIn("temp-cleanup", self.calls)


    def test_truthy_nonboolean_owner_proof_rejected_before_download(self):
        from dataclasses import replace
        for proof in ("yes", 1, ["owned"], {"owned": True}):
            with self.subTest(proof=proof):
                self.calls.clear()
                adapters = replace(self.adapters, verify_owner=lambda user, path, value=proof: value)
                with self.assertRaises(PermissionError):
                    finalize_authenticated("Bearer verified", self.body, adapters)
                self.assertEqual(self.calls, [])


    @patch("tests.video.finalize_core.verify", return_value={"duration": 2})
    def test_reconciliation_outage_preserves_video_and_uncertainty(self, verify):
        from dataclasses import replace
        def uncertain(*args):
            raise PostCommitUnknown("DB acknowledgement lost")
        def reconcile_down(*args):
            raise TimeoutError("DB reconciliation unavailable")
        adapters = replace(self.adapters, create_post=uncertain, reconcile_post=reconcile_down)
        with self.assertRaises(PostCommitUnknown):
            finalize_authenticated("Bearer verified", self.body, adapters)
        self.assertNotIn("delete", self.calls)
        self.assertIn("temp-cleanup", self.calls)

if __name__ == "__main__":
    unittest.main()

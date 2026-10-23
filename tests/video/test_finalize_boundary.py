import unittest
from unittest.mock import patch
from tests.video.finalize_boundary import ServerAdapters, finalize_authenticated
from tests.video.finalize_core import PostCommitUnknown

USER = "10000000-0000-0000-0000-000000000001"
PATH = USER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.adapters = ServerAdapters(
            authenticate_token=lambda token: USER if token == "verified" else (_ for _ in ()).throw(PermissionError()),
            verify_owner=lambda user, path: self.calls.append("owner") or (user == USER and path == PATH),
            download_staged=lambda user, path: self.calls.append("download") or "/tmp/test.mp4",
            create_post=lambda user, path, content: self.calls.append("post") or POST,
            delete_staged=lambda path: self.calls.append("delete"),
            reconcile_post=lambda user, path: None,
            enqueue_cleanup=lambda user, path: self.calls.append("queue"),
        )
        self.body = {"object_path": PATH, "content": "hello"}

    def test_no_bearer_rejected_before_storage(self):
        with self.assertRaises(PermissionError):
            finalize_authenticated("", self.body, self.adapters)
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
        self.assertEqual(self.calls, ["owner", "download", "owner", "post"])

    @patch("tests.video.finalize_core.verify", return_value={"duration": 2})
    def test_unknown_commit_never_deletes(self, verify):
        from dataclasses import replace
        adapters = replace(self.adapters, create_post=lambda *args: (_ for _ in ()).throw(PostCommitUnknown()))
        with self.assertRaises(PostCommitUnknown):
            finalize_authenticated("Bearer verified", self.body, adapters)
        self.assertNotIn("delete", self.calls)

if __name__ == "__main__":
    unittest.main()

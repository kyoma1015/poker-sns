import unittest
from unittest.mock import patch
from urllib.error import URLError
from tests.video.finalize_core import PostCommitUnknown
from tests.video.isolated_db_adapter import publish_post, reconcile_post

URL = "http://127.0.0.1:56321"
OWNER = "10000000-0000-0000-0000-000000000001"
PATH = OWNER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"

class IsolatedDbAdapterTests(unittest.TestCase):
    @patch("tests.video.isolated_db_adapter._rpc", return_value=POST)
    def test_publish_uses_isolated_rpc(self, rpc):
        self.assertEqual(publish_post(URL, "local-key", OWNER, PATH, "hi"), POST)
        self.assertEqual(rpc.call_args.args[2], "video_qa_publish")

    @patch("tests.video.isolated_db_adapter._rpc", side_effect=URLError("timeout"))
    def test_unknown_commit_never_claimed_failed(self, rpc):
        with self.assertRaises(PostCommitUnknown):
            publish_post(URL, "local-key", OWNER, PATH, "hi")

    @patch("tests.video.isolated_db_adapter._rpc", return_value=None)
    def test_uncommitted_reconciliation(self, rpc):
        self.assertIsNone(reconcile_post(URL, "local-key", OWNER, PATH))

    @patch("tests.video.isolated_db_adapter.urlopen")
    def test_reject_nonisolated_host(self, opener):
        from tests.video.isolated_db_adapter import _rpc
        with self.assertRaises(ValueError):
            _rpc("https://example.supabase.co", "key", "video_qa_publish", {})
        opener.assert_not_called()

if __name__ == "__main__":
    unittest.main()

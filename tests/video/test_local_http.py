import json
import threading
import unittest
from contextlib import contextmanager
from http.server import HTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from tests.video.finalize_boundary import ServerAdapters
from tests.video.local_http import make_handler

USER = "10000000-0000-0000-0000-000000000001"
POST = "40000000-0000-0000-0000-000000000001"
PATH = USER + "/30000000-0000-0000-0000-000000000001.mp4"

class HttpContractTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        @contextmanager
        def staged(user, path):
            self.calls.append("download")
            try:
                yield "/tmp/staged.mp4"
            finally:
                self.calls.append("cleanup")
        adapters = ServerAdapters(
            authenticate_token=lambda token: USER if token == "verified" else (_ for _ in ()).throw(PermissionError()),
            verify_owner=lambda user, path: user == USER and path == PATH,
            download_staged=staged,
            create_post=lambda user, path, content: POST,
            delete_staged=lambda path: self.calls.append("delete"),
            reconcile_post=lambda user, path: None,
            enqueue_cleanup=lambda user, path: self.calls.append("queue"),
        )
        self.server = HTTPServer(("127.0.0.1", 0), make_handler(adapters))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    def send(self, body, auth="Bearer verified"):
        request = Request(
            "http://127.0.0.1:%s/internal/video/finalize" % self.server.server_port,
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json", "Authorization": auth},
            method="POST",
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    @patch("tests.video.finalize_core.verify", return_value={"duration": 2})
    def test_valid_request(self, verify):
        status, data = self.send({"object_path": PATH, "content": "hello"})
        self.assertEqual((status, data), (200, {"post_id": POST}))
        self.assertEqual(self.calls, ["download", "cleanup"])

    def test_missing_auth_fails_closed(self):
        status, _ = self.send({"object_path": PATH, "content": ""}, auth="")
        self.assertEqual(status, 403)
        self.assertEqual(self.calls, [])

    def test_untrusted_user_id_rejected(self):
        status, _ = self.send({"object_path": PATH, "content": "", "user_id": USER})
        self.assertEqual(status, 403)
        self.assertEqual(self.calls, [])

    @patch("tests.video.finalize_core.verify", side_effect=ValueError("invalid video"))
    def test_invalid_video_reclaimed_and_temp_cleaned(self, verify):
        status, _ = self.send({"object_path": PATH, "content": ""})
        self.assertEqual(status, 403)
        self.assertEqual(self.calls, ["download", "delete", "cleanup"])

if __name__ == "__main__":
    unittest.main()

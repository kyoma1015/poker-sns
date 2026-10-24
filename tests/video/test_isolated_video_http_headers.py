"""HTTP parser regression tests: ambiguous credentials and body framing fail closed."""
import http.client
import json
import threading
import unittest
from tests.video.isolated_video_http import make_local_server

class IsolatedVideoHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_local_server("isolated-anon", "isolated-service")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def raw_request(self, method, path, headers, body=b""):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            conn.putrequest(method, path)
            for name, value in headers:
                conn.putheader(name, value)
            conn.endheaders(body)
            response = conn.getresponse()
            status = response.status
            response.read()
            return status
        finally:
            conn.close()

    def test_duplicate_authorization_rejected_on_both_routes(self):
        for method, path in (("GET", "/video?post_id=example"),
                             ("POST", "/video/finalize")):
            with self.subTest(method=method):
                headers = [("Authorization", "Bearer first"),
                           ("Authorization", "Bearer second")]
                if method == "POST":
                    headers += [("Content-Type", "application/json"),
                                ("Content-Length", "2")]
                self.assertEqual(self.raw_request(method, path, headers,
                                                  b"{}" if method == "POST" else b""), 401)

    def test_ambiguous_post_framing_rejected_before_auth_lookup(self):
        common = [("Authorization", "Bearer invalid"),
                  ("Content-Type", "application/json")]
        cases = (
            (common + [("Content-Length", "2"), ("Content-Length", "2")], b"{}"),
            (common + [("Transfer-Encoding", "chunked"), ("Content-Length", "2")], b"{}"),
            (common + [("Content-Length", "2"),
                       ("Content-Type", "application/json")], b"{}"),
            (common, b""),
        )
        for headers, body in cases:
            with self.subTest(headers=headers):
                self.assertEqual(self.raw_request("POST", "/video/finalize",
                                                  headers, body), 400)

if __name__ == "__main__":
    unittest.main()

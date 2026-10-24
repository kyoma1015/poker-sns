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

    def test_get_rejects_ambiguous_query_before_media_lookup(self):
        cases = (
            "/video?post_id=a&post_id=b",
            "/video?post_id=a&extra=b",
            "/video?post_id=",
            "/video?post_id=a;b=c",
            "/video?post_id=a#fragment",
        )
        for path in cases:
            with self.subTest(path=path):
                status = self.raw_request(
                    "GET", path, [("Authorization", "Bearer invalid")])
                self.assertIn(status, (400, 401))

    def test_malformed_json_rejected_before_auth_adapters(self):
        headers = [("Authorization", "Bearer invalid"),
                   ("Content-Type", "application/json")]
        for body in (b"{", b"not-json", b'{"object_path":'):
            with self.subTest(body=body):
                self.assertEqual(
                    self.raw_request("POST", "/video/finalize",
                                     headers + [("Content-Length", str(len(body)))],
                                     body), 400)

    def test_duplicate_json_keys_rejected_before_auth_adapters(self):
        headers = [("Authorization", "Bearer invalid"),
                   ("Content-Type", "application/json")]
        for body in (
            b'{"object_path":"first","object_path":"second"}',
            b'{"content":"a","content":"b"}',
            b'{"nested":{"x":1,"x":2}}',
        ):
            with self.subTest(body=body):
                self.assertEqual(
                    self.raw_request("POST", "/video/finalize",
                                     headers + [("Content-Length", str(len(body)))],
                                     body), 400)

    def test_nonstandard_json_constants_rejected_before_auth_adapters(self):
        headers = [("Authorization", "Bearer invalid"),
                   ("Content-Type", "application/json")]
        for body in (
            b'{"content":NaN}',
            b'{"content":Infinity}',
            b'{"content":-Infinity}',
            b'{"nested":[NaN]}',
        ):
            with self.subTest(body=body):
                self.assertEqual(
                    self.raw_request("POST", "/video/finalize",
                                     headers + [("Content-Length", str(len(body)))],
                                     body), 400)

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
                expected = 415 if sum(name.lower() == "content-type" for name, _ in headers) > 1 else 400
                self.assertEqual(self.raw_request("POST", "/video/finalize",
                                                  headers, body), expected)

if __name__ == "__main__":
    unittest.main()

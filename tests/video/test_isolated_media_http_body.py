"""Regression: media HTTP handler must actually write response bytes.

Previous source accidentally embedded literal \\n in a comment and commented
out self.wfile.write(data), yielding HTTP 200 + Content-Length but empty body.
"""
import inspect
import threading
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from unittest.mock import patch
from tests.video.isolated_authorized_media_http import make_local_server
import textwrap
import unittest
from tests.video.isolated_authorized_media_http import make_handler

class HttpResponseBodyRegression(unittest.TestCase):
    def test_handler_writes_body_in_executable_code(self):
        source = inspect.getsource(make_handler)
        self.assertNotIn(r"\\n            self.wfile.write(data)", source)
        self.assertIn("self.wfile.write(data)", source)
        import ast
        tree = ast.parse(textwrap.dedent(source))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "write"]
        self.assertTrue(calls, "no executable response body write")


    def test_actual_http_body_and_private_headers(self):
        server = make_local_server("anon", "service")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with patch("tests.video.isolated_authorized_media_http.fetch_visible_video", return_value=b"media-bytes") as fetch:
                req = Request("http://127.0.0.1:%d/video?post_id=post" % server.server_port,
                              headers={"Authorization": "Bearer jwt"})
                with urlopen(req, timeout=5) as response:
                    self.assertEqual(response.status, 200)
                    self.assertEqual(response.read(), b"media-bytes")
                    self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                    self.assertEqual(response.headers["Vary"], "Authorization")
                fetch.assert_called_once()
        finally:
            server.shutdown()
            server.server_close()

    def test_actual_http_private_denied_without_body(self):
        server = make_local_server("anon", "service")
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with patch("tests.video.isolated_authorized_media_http.fetch_visible_video", side_effect=PermissionError("private")):
                req = Request("http://127.0.0.1:%d/video?post_id=post" % server.server_port,
                              headers={"Authorization": "Bearer jwt"})
                with self.assertRaises(HTTPError) as raised:
                    urlopen(req, timeout=5)
                self.assertEqual(raised.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()

if __name__ == "__main__":
    unittest.main()

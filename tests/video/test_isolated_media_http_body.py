"""Regression: media HTTP handler must actually write response bytes.

Previous source accidentally embedded literal \\n in a comment and commented
out self.wfile.write(data), yielding HTTP 200 + Content-Length but empty body.
"""
import inspect
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

if __name__ == "__main__":
    unittest.main()

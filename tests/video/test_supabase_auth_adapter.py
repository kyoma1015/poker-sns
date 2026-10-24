import base64
import json
import time
import unittest
from unittest.mock import patch
from tests.video.supabase_auth_adapter import authenticate_supabase_token

URL = "https://isolated-test.supabase.co"
USER = "10000000-0000-0000-0000-000000000001"
def token(**overrides):
    claims = {"iss": URL + "/auth/v1", "aud": "authenticated", "exp": int(time.time()) + 600, "sub": USER}
    claims.update(overrides)
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return "header." + body + ".signature"

class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, *args): return json.dumps({"id": USER, "aud": "authenticated"}).encode()

class AuthAdapterTests(unittest.TestCase):
    @patch("tests.video.supabase_auth_adapter.urlopen", return_value=Response())
    def test_verified_identity(self, request):
        self.assertEqual(authenticate_supabase_token(token(), project_url=URL, anon_key="local-test-key"), USER)
        self.assertEqual(request.call_count, 1)

    @patch("tests.video.supabase_auth_adapter.urlopen")
    def test_wrong_issuer_no_network(self, request):
        with self.assertRaises(PermissionError):
            authenticate_supabase_token(token(iss="https://other.invalid/auth/v1"), project_url=URL, anon_key="key")
        request.assert_not_called()

    @patch("tests.video.supabase_auth_adapter.urlopen")
    def test_expired_no_network(self, request):
        with self.assertRaises(PermissionError):
            authenticate_supabase_token(token(exp=1), project_url=URL, anon_key="key")
        request.assert_not_called()

    @patch("tests.video.supabase_auth_adapter.urlopen")
    def test_wrong_audience_no_network(self, request):
        with self.assertRaises(PermissionError):
            authenticate_supabase_token(token(aud="anon"), project_url=URL, anon_key="key")
        request.assert_not_called()

    @patch("tests.video.supabase_auth_adapter.urlopen", side_effect=TimeoutError())
    def test_auth_server_failure_fails_closed(self, request):
        with self.assertRaises(PermissionError):
            authenticate_supabase_token(token(), project_url=URL, anon_key="key")

    @patch("tests.video.supabase_auth_adapter.urlopen", return_value=Response())
    def test_reject_insecure_project_url(self, request):
        with self.assertRaises(ValueError):
            authenticate_supabase_token(token(), project_url="http://isolated-test.supabase.co", anon_key="key")
        request.assert_not_called()

if __name__ == "__main__":
    unittest.main()

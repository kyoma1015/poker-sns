import unittest
from unittest.mock import patch
from tests.video.finalize_boundary import finalize_authenticated
from tests.video.isolated_composition import build_isolated_adapters

USER = "10000000-0000-0000-0000-000000000001"
PATH = USER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"

class IsolatedCompositionTests(unittest.TestCase):
    def test_cross_request_token_rejected(self):
        adapters = build_isolated_adapters(project_url="http://127.0.0.1:56321",
            anon_key="key",service_key="service",access_token="token-one")
        with self.assertRaises(PermissionError):
            finalize_authenticated("Bearer token-two",{"object_path":PATH,"content":""},adapters)

    @patch("tests.video.isolated_composition.authenticate_supabase_token",return_value=USER)
    @patch("tests.video.isolated_composition.download_private_staged")
    @patch("tests.video.isolated_composition.publish_post",return_value=POST)
    @patch("tests.video.finalize_core.verify")
    def test_composed_finalize(self, verify, publish, download, auth):
        from contextlib import contextmanager
        @contextmanager
        def local_file(*args,**kwargs):
            yield "/tmp/test-video.mp4"
        download.side_effect=local_file
        adapters = build_isolated_adapters(project_url="http://127.0.0.1:56321",
            anon_key="key",service_key="service",access_token="token-one")
        result=finalize_authenticated("Bearer token-one",{"object_path":PATH,"content":"hello"},adapters)
        self.assertEqual(result,{"post_id":POST})
        publish.assert_called_once()
        auth.assert_called_once()

if __name__ == "__main__":
    unittest.main()

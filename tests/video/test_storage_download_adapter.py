import io
import os
import unittest
from unittest.mock import patch
from tests.video.storage_download_adapter import download_private_staged, MAX_BYTES

USER = "10000000-0000-0000-0000-000000000001"
PATH = USER + "/30000000-0000-0000-0000-000000000001.mp4"
KW = {"project_url": "https://isolated-test.supabase.co", "anon_key": "key", "access_token": "jwt"}

class Response(io.BytesIO):
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): self.close()

class StorageDownloadTests(unittest.TestCase):
    @patch("tests.video.storage_download_adapter.urlopen", return_value=Response(b"media"))
    def test_download_and_temp_cleanup(self, opener):
        with download_private_staged(USER, PATH, **KW) as filename:
            with open(filename, "rb") as media_file:
                self.assertEqual(media_file.read(), b"media")
            self.assertTrue(os.path.exists(filename))
        self.assertFalse(os.path.exists(filename))
        self.assertIn("/storage/v1/object/authenticated/post-videos/", opener.call_args.args[0].full_url)

    @patch("tests.video.storage_download_adapter.urlopen")
    def test_cross_owner_no_network(self, opener):
        with self.assertRaises(PermissionError):
            with download_private_staged("20000000-0000-0000-0000-000000000002", PATH, **KW): pass
        opener.assert_not_called()

    @patch("tests.video.storage_download_adapter.urlopen", return_value=Response(b""))
    def test_empty_rejected(self, opener):
        with self.assertRaises(ValueError):
            with download_private_staged(USER, PATH, **KW): pass

    @patch("tests.video.storage_download_adapter.urlopen", return_value=Response(b"x" * (MAX_BYTES + 1)))
    def test_oversized_rejected(self, opener):
        with self.assertRaises(ValueError):
            with download_private_staged(USER, PATH, **KW): pass

if __name__ == "__main__":
    unittest.main()

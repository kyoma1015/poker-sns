"""Isolated media authorization race tests: fail closed after Storage fetch."""
import io
import json
import unittest
from unittest.mock import patch
from tests.video.isolated_authorized_media_proxy import fetch_visible_video, API

OWNER = "10000000-0000-0000-0000-000000000001"
VIEWER = "20000000-0000-0000-0000-000000000002"
POST = "30000000-0000-0000-0000-000000000003"
PATH = OWNER + "/40000000-0000-0000-0000-000000000004.mp4"

class Response:
    status = 200
    def __init__(self, body): self.stream = io.BytesIO(body)
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self, size=-1): return self.stream.read(size)

class MediaRaceTests(unittest.TestCase):
    def run_case(self, second):
        first = {"user_id": OWNER, "video_path": PATH, "is_public": True}
        responses = [Response(json.dumps([first]).encode()),
                     Response(b"media"),
                     Response(json.dumps(second).encode())]
        with patch("tests.video.isolated_authorized_media_proxy.authenticate_supabase_token", return_value=VIEWER), \
             patch("tests.video.isolated_authorized_media_proxy.urlopen", side_effect=responses):
            return fetch_visible_video(API, "anon", "service", "jwt", POST)

    def test_visibility_revoked_during_storage_read(self):
        with self.assertRaises(PermissionError):
            self.run_case([{"user_id": OWNER, "video_path": PATH, "is_public": False}])

    def test_media_path_replaced_during_storage_read(self):
        with self.assertRaises(PermissionError):
            self.run_case([{"user_id": OWNER, "video_path": OWNER + "/different.mp4", "is_public": True}])

    def test_post_removed_during_storage_read(self):
        with self.assertRaises(PermissionError):
            self.run_case([])

    def test_unchanged_public_post(self):
        self.assertEqual(self.run_case([{"user_id": OWNER, "video_path": PATH, "is_public": True}]), b"media")


    def test_malformed_acl_rows_fail_closed(self):
        responses = [Response(json.dumps({"not": "a list"}).encode())]
        with patch("tests.video.isolated_authorized_media_proxy.authenticate_supabase_token", return_value=VIEWER), \
             patch("tests.video.isolated_authorized_media_proxy.urlopen", side_effect=responses):
            with self.assertRaises(PermissionError):
                fetch_visible_video(API, "anon", "service", "jwt", POST)

    def test_viewer_identity_drift_fails_closed(self):
        first = {"user_id": OWNER, "video_path": PATH, "is_public": True}
        responses = [Response(json.dumps([first]).encode()), Response(b"media")]
        with patch("tests.video.isolated_authorized_media_proxy.authenticate_supabase_token", side_effect=[VIEWER, OWNER]), \
             patch("tests.video.isolated_authorized_media_proxy.urlopen", side_effect=responses):
            with self.assertRaises(PermissionError):
                fetch_visible_video(API, "anon", "service", "jwt", POST)

if __name__ == "__main__":
    unittest.main()

"""Isolated-only end-to-end composition contract: upload -> verify -> publish -> playback.

No production Supabase connection or deletion. A mock immutable Storage
enforces insert-once UUID paths and blocks UPDATE/DELETE, including ABA.
"""
import unittest
from unittest.mock import patch
from contextlib import contextmanager
from tests.video.finalize_boundary import finalize_authenticated
from tests.video.isolated_composition import build_isolated_adapters

OWNER = "10000000-0000-0000-0000-000000000001"
PATH = OWNER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"

class InsertOnceStorage:
    def __init__(self):
        self.objects = {}
    def insert(self, path, data):
        if path in self.objects:
            raise PermissionError("immutable collision")
        self.objects[path] = data
    def replace(self, path, data):
        raise PermissionError("UPDATE forbidden")
    def delete(self, path):
        raise PermissionError("DELETE forbidden")
    def read(self, path):
        return self.objects[path]

class IsolatedVideoEndToEnd(unittest.TestCase):
    def test_insert_once_replacement_and_playback(self):
        storage = InsertOnceStorage()
        storage.insert(PATH, b"isolated-video")
        with self.assertRaises(PermissionError):
            storage.insert(PATH, b"replacement")
        with self.assertRaises(PermissionError):
            storage.replace(PATH, b"replacement")
        with self.assertRaises(PermissionError):
            storage.delete(PATH)
        with patch("tests.video.isolated_composition.authenticate_supabase_token", return_value=OWNER), \
             patch("tests.video.isolated_composition.publish_post", return_value=POST), \
             patch("tests.video.finalize_core.verify"), \
             patch("tests.video.isolated_composition.download_private_staged") as download:
            @contextmanager
            def staged(*args, **kwargs):
                if storage.read(PATH) != b"isolated-video":
                    raise PermissionError("object replaced")
                yield "/tmp/isolated-video.mp4"
            download.side_effect = staged
            adapters = build_isolated_adapters(
                project_url="http://127.0.0.1:56321",
                anon_key="isolated", service_key="isolated", access_token="isolated-jwt")
            result = finalize_authenticated("Bearer isolated-jwt",
                {"object_path": PATH, "content": "test"}, adapters)
            self.assertEqual(result["post_id"], POST)
            self.assertEqual(storage.read(PATH), b"isolated-video")
            with self.assertRaises(RuntimeError):
                adapters.delete_staged(PATH)

if __name__ == "__main__":
    unittest.main()

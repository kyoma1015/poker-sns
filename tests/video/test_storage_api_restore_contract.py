"""Offline Storage REST contract rehearsal. Local mock only; no production or test Supabase."""
import hashlib
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from urllib.parse import unquote, urlsplit

TOKEN = "synthetic-backup-credential"
BUCKET = {"id": "post-videos", "public": False, "file_size_limit": 20971520}
OBJECT = ("post-videos", "user-1/sample.mp4")
PAYLOAD = b"synthetic-video-bytes"

class LocalStorageHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, payload=b"", content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def auth(self):
        return (self.headers.get("apikey") == TOKEN
                and self.headers.get("Authorization") == "Bearer " + TOKEN)

    def do_GET(self):
        if not self.auth():
            return self.reply(401)
        path = unquote(urlsplit(self.path).path)
        if path == "/storage/v1/bucket":
            return self.reply(200, json.dumps([BUCKET]).encode())
        if path == "/storage/v1/object/authenticated/" + OBJECT[0] + "/" + OBJECT[1]:
            if OBJECT not in self.server.objects:
                return self.reply(404)
            return self.reply(200, self.server.objects[OBJECT], "video/mp4")
        return self.reply(404)

    def do_POST(self):
        if not self.auth():
            return self.reply(401)
        path = unquote(urlsplit(self.path).path)
        if path == "/storage/v1/object/list/" + BUCKET["id"]:
            rows = [{"name": OBJECT[1], "id": "synthetic-object-1",
                     "updated_at": "synthetic-timestamp"}] if OBJECT in self.server.objects else []
            return self.reply(200, json.dumps(rows).encode())
        return self.reply(404)

    def do_PUT(self):
        if not self.auth():
            return self.reply(401)
        path = unquote(urlsplit(self.path).path)
        if path != "/storage/v1/object/" + OBJECT[0] + "/" + OBJECT[1]:
            return self.reply(404)
        size = int(self.headers.get("Content-Length", "0"))
        if size > BUCKET["file_size_limit"]:
            return self.reply(413)
        if OBJECT in self.server.objects:
            return self.reply(409)
        self.server.objects[OBJECT] = self.rfile.read(size)
        return self.reply(201, b'{"Key":"synthetic"}')

class MockStorageRestoreContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), LocalStorageHandler)
        cls.server.objects = {}
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    def setUp(self):
        self.server.objects = {}

    def request(self, method, path, body=None, authorized=True):
        headers = {"Content-Type": "application/octet-stream"}
        if authorized:
            headers.update({"apikey": TOKEN, "Authorization": "Bearer " + TOKEN})
        req = urllib.request.Request(self.base + path, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=4) as response:
                return response.status, response.read()
        except urllib.error.HTTPError as error:
            return error.code, error.read()

    def test_private_bucket_api_restore_and_db_metadata(self):
        expected_db_metadata = {
            "bucket_id": BUCKET["id"], "object_name": OBJECT[1],
            "owner": "user-1", "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
            "bytes": len(PAYLOAD), "public": False
        }
        status, buckets = self.request("GET", "/storage/v1/bucket")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(buckets)[0], BUCKET)
        upload_path = "/storage/v1/object/" + "/".join(OBJECT)
        status, _ = self.request("PUT", upload_path, PAYLOAD)
        self.assertEqual(status, 201)
        status, body = self.request("GET", "/storage/v1/object/authenticated/" + "/".join(OBJECT))
        self.assertEqual(status, 200)
        restored_metadata = {
            "bucket_id": BUCKET["id"], "object_name": OBJECT[1], "owner": "user-1",
            "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "public": BUCKET["public"]
        }
        self.assertEqual(restored_metadata, expected_db_metadata)
        status, listing = self.request("POST", "/storage/v1/object/list/" + BUCKET["id"], b"{}")
        self.assertEqual(status, 200)
        self.assertEqual(len(json.loads(listing)), 1)

    def test_unauthorized_read_write_and_list_are_denied(self):
        for method, path, body in [
            ("GET", "/storage/v1/bucket", None),
            ("GET", "/storage/v1/object/authenticated/" + "/".join(OBJECT), None),
            ("POST", "/storage/v1/object/list/" + BUCKET["id"], b"{}"),
            ("PUT", "/storage/v1/object/" + "/".join(OBJECT), PAYLOAD)
        ]:
            self.assertEqual(self.request(method, path, body, authorized=False)[0], 401)
        self.assertEqual(self.server.objects, {})

    def test_restore_will_not_replace_existing_object(self):
        path = "/storage/v1/object/" + "/".join(OBJECT)
        self.assertEqual(self.request("PUT", path, PAYLOAD)[0], 201)
        self.assertEqual(self.request("PUT", path, b"changed")[0], 409)
        self.assertEqual(self.server.objects[OBJECT], PAYLOAD)

    def test_size_limit_and_wrong_bucket(self):
        path = "/storage/v1/object/" + "/".join(OBJECT)
        self.assertEqual(self.request("PUT", path, b"x" * (BUCKET["file_size_limit"] + 1))[0], 413)
        self.assertEqual(self.request("PUT", "/storage/v1/object/other/user-1/sample.mp4", PAYLOAD)[0], 404)

if __name__ == "__main__":
    unittest.main()

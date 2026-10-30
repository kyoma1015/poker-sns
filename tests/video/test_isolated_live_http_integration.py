"""Live loopback HTTP integration of existing isolated Auth, Storage and RPC adapters.

This exercises actual HTTP transports and ffprobe, but the server is an
in-memory Supabase protocol fixture, NOT a real Supabase/PostgreSQL instance.
No remote service or production credentials are used.
"""
import base64
import json
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from tests.video.isolated_composition import build_isolated_adapters
from tests.video.finalize_boundary import finalize_authenticated

OWNER = "10000000-0000-0000-0000-000000000001"
PATH = OWNER + "/30000000-0000-0000-0000-000000000001.mp4"
POST = "40000000-0000-0000-0000-000000000001"
URL = "http://127.0.0.1:56321"

def token():
    claims = {"sub": OWNER, "aud": "authenticated", "iss": URL + "/auth/v1",
              "exp": int(time.time()) + 600}
    middle = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return "fixture." + middle + ".fixture"

class SupabaseFixture(BaseHTTPRequestHandler):
    media = b""
    published = {}
    def log_message(self, *args):
        pass
    def _authorized(self):
        return self.headers.get("Authorization") == "Bearer " + self.server.token
    def _reply(self, status, payload, mime="application/json"):
        data = json.dumps(payload).encode() if mime == "application/json" else payload
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
    def do_GET(self):
        if not self._authorized():
            return self._reply(401, {"error": "unauthorized"})
        if self.path == "/auth/v1/user":
            return self._reply(200, {"id": OWNER, "aud": "authenticated"})
        if self.path == "/storage/v1/object/authenticated/post-videos/" + PATH:
            return self._reply(200, self.media, "video/mp4")
        return self._reply(404, {"error": "not_found"})
    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer isolated-service":
            return self._reply(403, {"error": "service_role_required"})
        length = int(self.headers.get("Content-Length", "0"))
        data = json.loads(self.rfile.read(length))
        if self.path == "/rest/v1/rpc/video_qa_publish":
            if data.get("p_owner") != OWNER or data.get("p_path") != PATH:
                return self._reply(403, {"error": "owner_mismatch"})
            prior = self.published.get(PATH)
            if prior and prior != data["p_content"]:
                return self._reply(409, {"error": "content_conflict"})
            self.published[PATH] = data["p_content"]
            return self._reply(200, POST)
        if self.path == "/rest/v1/rpc/video_qa_reconcile":
            return self._reply(200, POST if PATH in self.published else None)
        return self._reply(404, {"error": "unknown_rpc"})

@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg/ffprobe required")
class LiveHttpVideoIntegration(unittest.TestCase):
    def test_real_http_auth_storage_ffprobe_rpc_and_reconcile(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "sample.mp4"
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                "-i", "color=c=black:s=32x32:r=5", "-t", "1", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-y", str(file)], check=True, timeout=20)
            SupabaseFixture.media = file.read_bytes()
            SupabaseFixture.published = {}
            with ThreadingHTTPServer(("127.0.0.1", 56321), SupabaseFixture) as server:
                server.token = token()
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    adapters = build_isolated_adapters(project_url=URL,
                        anon_key="isolated-anon", service_key="isolated-service",
                        access_token=server.token)
                    first = finalize_authenticated("Bearer " + server.token,
                        {"object_path": PATH, "content": "hello"}, adapters)
                    second = finalize_authenticated("Bearer " + server.token,
                        {"object_path": PATH, "content": "hello"}, adapters)
                    self.assertEqual(first, {"post_id": POST})
                    self.assertEqual(second, first)
                    self.assertEqual(SupabaseFixture.published[PATH], "hello")
                    self.assertEqual(adapters.reconcile_post(OWNER, PATH), POST)
                    # Authorized Storage media delivery is a live HTTP GET;
                    # this is NOT the Vercel post-visibility media endpoint.
                    media_url = URL + "/storage/v1/object/authenticated/post-videos/" + PATH
                    with urlopen(Request(media_url, headers={"Authorization": "Bearer " + server.token}), timeout=5) as media_response:
                        self.assertEqual(media_response.status, 200)
                        self.assertEqual(media_response.read(), SupabaseFixture.media)
                    with self.assertRaises(HTTPError) as denied:
                        urlopen(Request(media_url, headers={"Authorization": "Bearer invalid"}), timeout=5)
                    self.assertEqual(denied.exception.code, 401)
                    with self.assertRaises(PermissionError):
                        finalize_authenticated("Bearer wrong",
                            {"object_path": PATH, "content": "hello"}, adapters)
                    with self.assertRaises(RuntimeError):
                        adapters.delete_staged(PATH)
                finally:
                    server.shutdown()
                    thread.join(timeout=5)

if __name__ == "__main__":
    unittest.main()

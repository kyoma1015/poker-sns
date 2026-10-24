"""Isolated-only authenticated HTTP POST boundary for video finalization.

This is a local QA adapter, not a production route. Service credentials remain
server-side; caller identity comes exclusively from verified Supabase Auth.
"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .finalize_boundary import finalize_authenticated
from .isolated_composition import build_isolated_adapters

API = "http://127.0.0.1:56321"
MAX_JSON_BYTES = 12 * 1024

def make_handler(anon_key: str, service_key: str):
    if not anon_key or not service_key:
        raise PermissionError("isolated server credentials required")
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/video/finalize":
                self.send_error(404)
                return
            authorization = self.headers.get("Authorization", "")
            if (not authorization.startswith("Bearer ") or
                    not authorization[7:] or authorization[7:].strip() != authorization[7:]):
                self.send_error(401)
                return
            if self.headers.get("Content-Type", "").lower() != "application/json":
                self.send_error(415)
                return
            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length)
            except (TypeError, ValueError):
                self.send_error(400)
                return
            if length <= 0 or length > MAX_JSON_BYTES:
                self.send_error(413)
                return
            try:
                body = json.loads(self.rfile.read(length))
                adapters = build_isolated_adapters(
                    project_url=API, anon_key=anon_key, service_key=service_key,
                    access_token=authorization[7:])
                result = finalize_authenticated(authorization, body, adapters)
            except (PermissionError, ValueError, TypeError, KeyError):
                self.send_error(403)
                return
            except Exception:
                self.send_error(503)
                return
            payload = json.dumps(result).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store, private")
            self.send_header("Vary", "Authorization")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(payload)
        def log_message(self, *args):
            pass
    return Handler

def make_local_server(anon_key: str, service_key: str):
    return ThreadingHTTPServer(("127.0.0.1", 0), make_handler(anon_key, service_key))

"""Local-only HTTP handler for isolated video finalize contract tests.

This is NOT a production endpoint. It must never be deployed with mock adapters.
Production JWT verification, immutable Storage reads, transactional DB adapters,
durable cleanup and viewer authorization are required before activation.
"""
import json
from http.server import BaseHTTPRequestHandler
from .finalize_boundary import finalize_authenticated

MAX_REQUEST_BYTES = 12 * 1024

def make_handler(adapters):
    class FinalizeHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/internal/video/finalize":
                self.send_error(404)
                return
            length = self.headers.get("Content-Length", "")
            if not length.isdigit() or int(length) > MAX_REQUEST_BYTES:
                self.send_error(413)
                return
            try:
                payload = json.loads(self.rfile.read(int(length)))
                result = finalize_authenticated(self.headers.get("Authorization", ""), payload, adapters)
                code, response = 200, result
            except (PermissionError, ValueError, TypeError, json.JSONDecodeError):
                code, response = 403, {"error": "request rejected"}
            except Exception:
                code, response = 503, {"error": "finalization unavailable"}
            encoded = json.dumps(response).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        def log_message(self, format, *args):
            pass
    return FinalizeHandler

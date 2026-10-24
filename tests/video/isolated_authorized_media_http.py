"""Isolated-only HTTP endpoint for per-request authorized video delivery.

No public deployment: the local handler keeps the service key server-side,
requires the caller's JWT on every request, and never redirects to a signed
Storage URL. All media is bounded by the existing 20 MiB policy.
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from .isolated_authorized_media_proxy import fetch_visible_video

def make_handler(anon_key: str, service_key: str):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlsplit(self.path)
            if parsed.path != "/video":
                self.send_error(404)
                return
            # Reject URL fragments and semicolon query separators rather than
            # accepting ambiguous representations of a privileged media request.
            if parsed.fragment or ";" in parsed.query:
                self.send_error(400)
                return
            params = parse_qs(parsed.query, keep_blank_values=True)
            post_ids = params.get("post_id", [])
            auth_headers = self.headers.get_all("Authorization", [])
            if len(auth_headers) != 1:
                self.send_error(401)
                return
            authorization = auth_headers[0]
            if (set(params) != {"post_id"} or len(post_ids) != 1
                    or not post_ids[0] or not authorization.startswith("Bearer ")
                    or not authorization[7:] or authorization[7:].strip() != authorization[7:]):
                self.send_error(401)
                return
            try:
                data = fetch_visible_video("http://127.0.0.1:56321",
                                           anon_key, service_key,
                                           authorization[7:], post_ids[0])
            except (PermissionError, ValueError, KeyError):
                self.send_error(403)
                return
            except Exception:
                self.send_error(503)
                return
            self.send_response(200)
            self.send_header("Content-Type", "video/webm" if data[:4] == b"\x1aE\xdf\xa3" else "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store, private")
            self.send_header("Pragma", "no-cache")
            self.send_header("Vary", "Authorization")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            # Authorization is checked before headers. Once bytes are sent,
            # in-flight revocation cannot be guaranteed.
            self.wfile.write(data)
        def log_message(self, *args):
            pass
    return Handler

def make_local_server(anon_key: str, service_key: str):
    return ThreadingHTTPServer(("127.0.0.1", 0),
                               make_handler(anon_key, service_key))

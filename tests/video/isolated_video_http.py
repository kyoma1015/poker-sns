"""Local-only combined video HTTP handler; never deploy to production.

Compose the already tested JWT-authenticated finalization and per-request
authorized playback handlers on one loopback server. No signed URL exposure.
"""
from http.server import ThreadingHTTPServer
from .isolated_finalize_http import make_handler as finalize_handler
from .isolated_authorized_media_http import make_handler as media_handler

def make_local_server(anon_key: str, service_key: str):
    # Both factories validate only isolated credentials and create handlers;
    # the combined server is bound exclusively to loopback.
    post = finalize_handler(anon_key, service_key)
    get = media_handler(anon_key, service_key)
    handler = type("IsolatedVideoHandler", (post, get), {})
    return ThreadingHTTPServer(("127.0.0.1", 0), handler)

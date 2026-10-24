"""Private staged-object download adapter for an isolated trusted server.

Uses the authenticated user's JWT, not a service-role key. The caller must
validate ownership and hold a storage object lock/version to prevent TOCTOU.
Never wire this prototype to production until atomic object identity is proven.
"""
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID
import os

MAX_BYTES = 20 * 1024 * 1024

@contextmanager
def download_private_staged(
    user_id: str, object_path: str, *,
    project_url: str, anon_key: str, access_token: str,
    allow_local_isolated: bool = False,
):
    uid = str(UUID(user_id))
    parts = object_path.split("/")
    if len(parts) != 2 or parts[0] != uid:
        raise PermissionError("owner mismatch")
    from uuid import UUID as ParseUUID
    stem, dot, ext = parts[1].rpartition(".")
    if not dot or ext not in ("mp4", "webm"):
        raise ValueError("unsupported object path")
    ParseUUID(stem)
    parsed = urlparse(project_url)
    local_ok = allow_local_isolated and (parsed.scheme, parsed.hostname, parsed.port) == ("http", "127.0.0.1", 56321)
    valid_url = (parsed.scheme == "https" or local_ok) and bool(parsed.hostname) and not (parsed.username or parsed.password or parsed.query or parsed.fragment) and parsed.path in ("", "/")
    if not valid_url or not anon_key or not access_token:
        raise PermissionError("private storage credentials required")
    url = project_url.rstrip("/") + "/storage/v1/object/authenticated/post-videos/" + quote(object_path, safe="/")
    request = Request(url, headers={"Authorization": "Bearer " + access_token, "apikey": anon_key})
    path = None
    try:
        with urlopen(request, timeout=20) as response:
            if response.status != 200:
                raise PermissionError("private storage denied")
            with NamedTemporaryFile(prefix="poker-video-", suffix="." + ext, delete=False) as tmp:
                path = tmp.name
                total = 0
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError("video exceeds 20 MiB")
                    tmp.write(chunk)
        if total == 0:
            raise ValueError("empty video")
        yield path
    finally:
        if path is not None:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

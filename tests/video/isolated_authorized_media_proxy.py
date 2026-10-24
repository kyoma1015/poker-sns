"""Isolated private media proxy: authorize on EVERY request, no signed URLs.

A privacy change takes effect on the next request; an already streaming
response cannot be revoked. The prototype is intentionally local-only.
"""
import json
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID
from .supabase_auth_adapter import authenticate_supabase_token

API = "http://127.0.0.1:56321"
MAX_BYTES = 20 * 1024 * 1024

def fetch_visible_video(project_url: str, anon_key: str, service_key: str,
                        viewer_token: str, post_id: str) -> bytes:
    if project_url != API or not anon_key or not service_key:
        raise PermissionError("isolated server only")
    viewer = authenticate_supabase_token(
        viewer_token, project_url=API, anon_key=anon_key,
        allow_local_isolated=True)
    query = urlencode({"id": "eq." + str(UUID(post_id)),
                       "select": "user_id,video_path,is_public"})
    req = Request(API + "/rest/v1/posts?" + query,
                  headers={"apikey": anon_key,
                           "Authorization": "Bearer " + viewer_token})
    with urlopen(req, timeout=10) as response:
        rows = json.load(response)
    if len(rows) != 1:
        raise PermissionError("post hidden by RLS")
    post = rows[0]
    owner = post["user_id"]
    if viewer != owner and post.get("is_public") is not True:
        raise PermissionError("private post")
    path = post.get("video_path")
    if not isinstance(path, str) or not path.startswith(owner + "/") or path.count("/") != 1:
        raise PermissionError("invalid storage path")
    req = Request(API + "/storage/v1/object/authenticated/post-videos/" +
                  quote(path, safe="/"),
                  headers={"apikey": service_key,
                           "Authorization": "Bearer " + service_key})
    with urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise PermissionError("Storage denied media")
        data = response.read(MAX_BYTES + 1)
    if not data or len(data) > MAX_BYTES:
        raise ValueError("invalid media size")
    return data

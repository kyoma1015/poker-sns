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
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise PermissionError("post hidden by RLS")
    post = rows[0]
    try:
        owner = str(UUID(post["user_id"]))
    except (KeyError, ValueError, TypeError):
        raise PermissionError("invalid post owner") from None
    if viewer != owner and post.get("is_public") is not True:
        raise PermissionError("private post")
    # Require a strict boolean even for the owner.
    if type(post.get("is_public")) is not bool:
        raise PermissionError("invalid visibility state")
    path = post.get("video_path")
    if not isinstance(path, str) or not path.startswith(owner + "/") or path.count("/") != 1:
        raise PermissionError("invalid storage path")
    # A post may reference only a staged video object, never arbitrary Storage keys.
    name = path.split("/", 1)[1]
    stem, separator, extension = name.rpartition(".")
    if not separator or extension not in ("mp4", "webm"):
        raise PermissionError("invalid video object")
    try:
        UUID(stem)
    except (ValueError, TypeError):
        raise PermissionError("invalid video object") from None
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
    # Re-check authorization AFTER Storage retrieval and BEFORE handing bytes
    # to the HTTP response. This closes the obvious visibility-flip window
    # during a slow download; it cannot revoke an already-sent response.
    if authenticate_supabase_token(
        viewer_token, project_url=API, anon_key=anon_key,
        allow_local_isolated=True) != viewer:
        raise PermissionError("viewer identity changed")
    with urlopen(req_for_visibility(post_id, anon_key, viewer_token), timeout=10) as response:
        fresh_rows = json.load(response)
    if not isinstance(fresh_rows, list) or len(fresh_rows) != 1 or not isinstance(fresh_rows[0], dict) or fresh_rows[0].get("user_id") != owner or fresh_rows[0].get("video_path") != path:
        raise PermissionError("post changed during media retrieval")
    if type(fresh_rows[0].get("is_public")) is not bool:
        raise PermissionError("invalid refreshed visibility state")
    if viewer != owner and fresh_rows[0].get("is_public") is not True:
        raise PermissionError("post became private during media retrieval")
    return data

def req_for_visibility(post_id: str, anon_key: str, viewer_token: str):
    query = urlencode({"id": "eq." + str(UUID(post_id)),
                       "select": "user_id,video_path,is_public"})
    return Request(API + "/rest/v1/posts?" + query,
                   headers={"apikey": anon_key,
                            "Authorization": "Bearer " + viewer_token})

"""Isolated-only viewer-authorized signing for public video posts.

The caller's JWT is checked against PostgREST RLS; server signing uses the
isolated service key only after that authorization. Never deploy this
prototype or expose service credentials to the browser.
"""
import json
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID
from .supabase_auth_adapter import authenticate_supabase_token

API = "http://127.0.0.1:56321"

def issue_visible_video_url(project_url: str, anon_key: str, service_key: str,
                            viewer_token: str, post_id: str, ttl: int = 60) -> str:
    if project_url != API or not anon_key or not service_key:
        raise PermissionError("isolated server credentials required")
    if type(ttl) is not int or not 1 <= ttl <= 60:
        raise ValueError("invalid lifetime")
    viewer = authenticate_supabase_token(
        viewer_token, project_url=API, anon_key=anon_key, allow_local_isolated=True)
    query = urlencode({"id": "eq." + str(UUID(post_id)),
                       "select": "user_id,video_path,is_public"})
    req = Request(API + "/rest/v1/posts?" + query,
                  headers={"apikey": anon_key,
                           "Authorization": "Bearer " + viewer_token})
    with urlopen(req, timeout=10) as response:
        rows = json.load(response)
    if len(rows) != 1:
        raise PermissionError("post not visible under RLS")
    post = rows[0]
    owner = post["user_id"]
    if owner != viewer and post.get("is_public") is not True:
        raise PermissionError("private post")
    path = post.get("video_path")
    if not isinstance(path, str) or not path.startswith(owner + "/") or path.count("/") != 1:
        raise PermissionError("invalid post object path")
    req = Request(API + "/storage/v1/object/sign/post-videos/" + quote(path, safe="/"),
                  data=json.dumps({"expiresIn": ttl}).encode(),
                  headers={"apikey": service_key,
                           "Authorization": "Bearer " + service_key,
                           "Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as response:
        result = json.load(response)
    signed = result.get("signedURL") or result.get("signedUrl")
    if not isinstance(signed, str) or not signed.startswith("/"):
        raise RuntimeError("invalid signed URL")
    return API + (signed if signed.startswith("/storage/v1/") else "/storage/v1" + signed)

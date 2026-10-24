"""Isolated video URL issuance, fail closed until reviewed public visibility.

Authenticates the caller with Supabase Auth, checks post visibility using
the caller's own RLS-scoped PostgREST query, then asks Storage to sign using
the same caller JWT. Never signs with a service-role credential.
"""
import json
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from uuid import UUID
from .supabase_auth_adapter import authenticate_supabase_token

def issue_owner_video_url(project_url: str, anon_key: str, access_token: str,
                          post_id: str, ttl: int = 60) -> str:
    if not isinstance(ttl, int) or isinstance(ttl, bool) or not 1 <= ttl <= 60:
        raise ValueError("invalid video URL lifetime")
    # Only the fixed isolated local stack is supported by this prototype.
    if project_url != "http://127.0.0.1:56321":
        raise ValueError("isolated URL required")
    viewer = authenticate_supabase_token(
        access_token, project_url=project_url, anon_key=anon_key,
        allow_local_isolated=True,
    )
    post = str(UUID(post_id))
    query = urlencode({"id": "eq." + post, "select": "user_id,video_path"})
    req = Request(project_url + "/rest/v1/posts?" + query,
                  headers={"apikey": anon_key,
                           "Authorization": "Bearer " + access_token})
    with urlopen(req, timeout=10) as response:
        rows = json.load(response)
    if len(rows) != 1 or rows[0].get("user_id") != viewer:
        raise PermissionError("video is not accessible to this viewer")
    path = rows[0].get("video_path")
    if not isinstance(path, str) or not path.startswith(viewer + "/"):
        raise PermissionError("video owner path mismatch")
    req = Request(project_url + "/storage/v1/object/sign/post-videos/" +
                  quote(path, safe="/"),
                  data=json.dumps({"expiresIn": ttl}).encode(),
                  headers={"apikey": anon_key,
                           "Authorization": "Bearer " + access_token,
                           "Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as response:
        result = json.load(response)
    signed = result.get("signedURL") or result.get("signedUrl")
    if not isinstance(signed, str) or not signed.startswith("/"):
        raise RuntimeError("unexpected signed URL response")
    return project_url + (signed if signed.startswith("/storage/v1/") else "/storage/v1" + signed)

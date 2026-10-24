"""Fail-closed video finalization core for a trusted server (not an HTTP endpoint).

The caller MUST authenticate a real Supabase JWT, pass the authenticated user ID,
and supply adapters scoped to that identity. Never accept user_id from request body.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

class PostCommitUnknown(RuntimeError):
    """The DB outcome is ambiguous: retain the video until reconciled."""

from .server_validate import verify

@dataclass(frozen=True)
class FinalizeRequest:
    authenticated_user_id: str
    object_path: str
    local_staged_file: str
    content: str

def finalize_video(
    request: FinalizeRequest,
    *,
    verify_owner: Callable[[str, str], bool],
    create_post: Callable[[str, str, str], str],
    delete_staged_object: Callable[[str], None],
) -> str:
    """Validate staged bytes, then persist. Fail closed and reclaim on failure.

    Caller must ensure create_post is atomic and authorizes its user ID.
    A failed cleanup is raised and must be retried by a durable orphan sweeper.
    """
    from uuid import UUID
    user_id = str(UUID(request.authenticated_user_id))
    segments = request.object_path.split("/")
    if len(segments) != 2 or segments[0] != user_id:
        raise ValueError("owner path mismatch")
    stem, dot, ext = segments[1].rpartition(".")
    if not dot or ext not in ("mp4", "webm"):
        raise ValueError("invalid object extension")
    UUID(stem)
    # Ownership must be proven before any destructive cleanup.
    if verify_owner(user_id, request.object_path) is not True:
        raise PermissionError("staged object not owned by authenticated user")
    try:
        verify(request.local_staged_file)
        return create_post(user_id, request.object_path, request.content)
    except PostCommitUnknown:
        # A timeout after commit must not delete media referenced by a post.
        # Reconciliation must check DB state before any cleanup.
        raise
    except Exception:
        delete_staged_object(request.object_path)
        raise


def finalize_http_request(headers, body, *, authenticate_jwt, download_staged,
                          verify_owner, create_post, delete_staged_object):
    """Transport-independent HTTP finalize handler for a trusted server.

    All injected adapters must be server-side. authenticate_jwt MUST validate
    signature, issuer, audience, expiry and subject against the Supabase JWKS.
    create_post MUST be an atomic, owner-scoped, idempotent DB operation.
    download_staged MUST return a trusted local copy of the exact Storage object.
    delete_staged_object MUST use an atomic conditional delete, never a blind
    path-only delete. This adapter is NOT production-wired.
    """
    import json
    import re
    from uuid import UUID
    if not isinstance(headers, dict) or not isinstance(body, (bytes, bytearray)):
        return 400, {"error": "invalid_request"}
    if len(body) > 4096:
        return 413, {"error": "request_too_large"}
    authorization = headers.get("authorization", "")
    if not isinstance(authorization, str):
        return 401, {"error": "unauthorized"}
    match = re.fullmatch(r"Bearer ([A-Za-z0-9_.-]+)", authorization)
    if match is None:
        return 401, {"error": "unauthorized"}
    try:
        user_id = str(UUID(authenticate_jwt(match.group(1))))
    except Exception:
        # JWT/JWKS verification failures must never reach Storage or DB.
        return 401, {"error": "unauthorized"}
    try:
        payload = json.loads(body)
        if not isinstance(payload, dict) or set(payload) != {"object_path", "content"}:
            raise ValueError("invalid fields")
        object_path, content = payload["object_path"], payload["content"]
        if not isinstance(object_path, str) or not isinstance(content, str):
            raise ValueError("invalid field type")
        if len(content) > 5000:
            raise ValueError("content too long")
        if not object_path.startswith(user_id + "/"):
            raise PermissionError("owner mismatch")
    except (ValueError, TypeError, UnicodeDecodeError, PermissionError):
        return 400, {"error": "invalid_request"}
    # Prove ownership BEFORE downloading; do not trust caller-provided file paths.
    try:
        if verify_owner(user_id, object_path) is not True:
            return 403, {"error": "forbidden"}
        with download_staged(user_id, object_path) as local_file:
            post_id = finalize_video(
                FinalizeRequest(user_id, object_path, str(local_file), content),
                verify_owner=verify_owner, create_post=create_post,
                delete_staged_object=delete_staged_object)
        return 201, {"post_id": str(post_id)}
    except PostCommitUnknown:
        return 503, {"error": "commit_unknown_retry_with_same_object"}
    except (PermissionError, ValueError):
        return 403, {"error": "forbidden_or_invalid_media"}
    except Exception:
        # Never expose Storage, database, or authentication internals.
        return 503, {"error": "temporarily_unavailable"}

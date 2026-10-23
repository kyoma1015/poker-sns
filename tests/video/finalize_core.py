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
    if not verify_owner(user_id, request.object_path):
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

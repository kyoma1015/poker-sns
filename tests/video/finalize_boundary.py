"""Isolated HTTP-facing finalization boundary. NOT deployed or wired to client.

All privileged operations must be supplied by a trusted server. In particular,
authenticate_token MUST verify Supabase JWT signature, issuer, audience and expiry
against the configured project, not merely decode the token.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from uuid import UUID
from contextlib import contextmanager
from .finalize_core import FinalizeRequest, finalize_video, PostCommitUnknown

@dataclass(frozen=True)
class ServerAdapters:
    authenticate_token: Callable[[str], str]
    verify_owner: Callable[[str, str], bool]
    download_staged: Callable[[str, str], object]
    create_post: Callable[[str, str, str], str]
    delete_staged: Callable[[str], None]
    reconcile_post: Callable[[str, str], str | None]
    enqueue_cleanup: Callable[[str, str], None]

def finalize_authenticated(
    authorization: str, body: dict, adapters: ServerAdapters
) -> dict:
    """Server boundary: fail closed; never trust a caller-supplied user ID.

    Storage download MUST be private, bounded, and pinned to immutable object
    identity to avoid TOCTOU replacement. The adapter owns temporary-file cleanup.
    Durable cleanup must be persisted before returning an unsuccessful result.
    """
    if not isinstance(authorization, str) or not authorization.startswith("Bearer "):
        raise PermissionError("Bearer token required")
    token = authorization[7:]
    if not token or token.strip() != token:
        raise PermissionError("invalid Bearer token")
    user_id = str(UUID(adapters.authenticate_token(token)))
    if not isinstance(body, dict) or set(body) != {"object_path", "content"}:
        raise ValueError("unexpected request fields")
    path, content = body["object_path"], body["content"]
    if not isinstance(path, str) or not isinstance(content, str) or len(content) > 10000:
        raise ValueError("invalid request body")
    segments = path.split("/")
    if len(segments) != 2 or segments[0] != user_id:
        raise PermissionError("owner path mismatch")
    if adapters.verify_owner(user_id, path) is not True:
        raise PermissionError("staged object not owned")
    # The adapter must return a context manager that removes temporary bytes.
    with adapters.download_staged(user_id, path) as local_file:
        try:
            post_id = finalize_video(
                FinalizeRequest(user_id, path, local_file, content),
                verify_owner=adapters.verify_owner,
                create_post=adapters.create_post,
                delete_staged_object=adapters.delete_staged,
            )
        except PostCommitUnknown:
            # Reconciliation can fail independently of the DB write. Preserve
            # the original uncertain outcome and NEVER trigger a delete.
            try:
                existing = adapters.reconcile_post(user_id, path)
            except Exception:
                raise PostCommitUnknown("reconciliation unavailable") from None
            if existing is None:
                # Do not delete while commit state is uncertain.
                raise
            post_id = existing
        return {"post_id": str(UUID(post_id))}

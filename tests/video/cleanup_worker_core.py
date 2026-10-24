"""Durable cleanup decision rules for isolated video workers.

The DB queue must persist jobs before acknowledgement. Worker adapters must
lock a row, reconcile committed posts, and verify Storage object identity
before any delete. This module does not perform production cleanup.
"""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class CleanupJob:
    owner_id: str
    object_path: str
    expected_object_version: str

def process_cleanup(
    job: CleanupJob, *,
    find_post: Callable[[str, str], str | None],
    get_object_version: Callable[[str], str | None],
    delete_if_version: Callable[[str, str], bool],
    mark_complete: Callable[[CleanupJob, str], None],
    reschedule: Callable[[CleanupJob, str], None],
) -> str:
    from uuid import UUID
    try:
        if str(UUID(job.owner_id)) != job.owner_id:
            raise ValueError("noncanonical owner")
        owner, name = job.object_path.split("/")
        stem, dot, extension = name.rpartition(".")
        if owner != job.owner_id or not dot or extension not in ("mp4", "webm") or str(UUID(stem)) != stem:
            raise ValueError("invalid object path")
    except (ValueError, TypeError, AttributeError):
        reschedule(job, "invalid owner or object path")
        return "RETRY"
    if not isinstance(job.expected_object_version, str) or not job.expected_object_version.strip():
        reschedule(job, "missing immutable object identity")
        return "RETRY"
    if find_post(job.owner_id, job.object_path) is not None:
        mark_complete(job, "post committed: retained")
        return "RETAINED"
    current = get_object_version(job.object_path)
    if current is None:
        mark_complete(job, "already absent")
        return "ABSENT"
    if current != job.expected_object_version:
        reschedule(job, "object version changed")
        return "RETRY"
    try:
        if not delete_if_version(job.object_path, current):
            reschedule(job, "conditional deletion unavailable or failed")
            return "RETRY"
    except Exception:
        reschedule(job, "conditional deletion raised")
        return "RETRY"
    mark_complete(job, "deleted")
    return "DELETED"

"""Conservative orphan-video recovery policy.

The Storage HTTP API has no verified atomic compare-and-delete. This module
makes the permanent no-reuse fence explicit without claiming that a database
reservation alone prevents service-role Storage writes. No deletion occurs.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class OrphanEvidence:
    post_exists: bool
    version_pinned: bool
    atomic_delete_supported: bool
    exclusive_write_lock: bool = False
    key_permanently_reserved: bool = False
    all_storage_writers_fenced: bool = False


def orphan_recovery_decision(*, post_exists: bool, version_pinned: bool,
                             atomic_delete_supported: bool,
                             exclusive_write_lock: bool = False,
                             key_permanently_reserved: bool = False,
                             all_storage_writers_fenced: bool = False) -> str:
    if post_exists:
        return "retain_posted"
    if not version_pinned:
        return "quarantine_no_version"
    if not key_permanently_reserved:
        return "quarantine_key_reuse_possible"
    if not all_storage_writers_fenced:
        return "quarantine_unfenced_storage_writers"
    if not atomic_delete_supported:
        return "quarantine_no_atomic_delete"
    if not exclusive_write_lock:
        return "quarantine_no_exclusive_lock"
    # A reservation, exclusive lock and version-aware API must be verified
    # against the actual Storage backend. This is review-only, never delete.
    return "eligible_for_review_only"

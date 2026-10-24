"""Isolation-only orphan recovery runbook (no destructive operation).

Automatic cleanup is disabled while object-version conditional delete is
unverified. Queue leases are not Storage object locks. A production recovery
plan must separately fence uploads, publication, and Storage writes.
"""
from .isolated_orphan_recovery_policy import orphan_recovery_decision

def plan_orphan_recovery(post_exists: bool, pinned_version: str | None,
                         storage_atomic_cas: bool, global_write_fence: bool):
    decision = orphan_recovery_decision(
        post_exists=post_exists,
        version_pinned=bool(pinned_version),
        atomic_delete_supported=storage_atomic_cas,
        exclusive_write_lock=global_write_fence)
    return {
        "decision": decision,
        "delete_permitted": False,
        "requires": ("verified Storage CAS delete, global write fencing, "
                     "fresh DB reconciliation and operator approval"),
    }

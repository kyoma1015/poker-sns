"""Isolation-only orphan recovery plan; never authorizes deletion.

Queue leases are not Storage locks. Permanent key reservation and all writer
fencing require independent evidence, not an operator-supplied assertion.
"""
from .isolated_orphan_recovery_policy import orphan_recovery_decision

def plan_orphan_recovery(post_exists: bool, pinned_version: str | None,
                         storage_atomic_cas: bool, global_write_fence: bool,
                         permanent_key_reservation: bool = False,
                         all_storage_writers_fenced: bool = False):
    decision = orphan_recovery_decision(
        post_exists=post_exists,
        version_pinned=bool(pinned_version),
        atomic_delete_supported=storage_atomic_cas,
        exclusive_write_lock=global_write_fence,
        key_permanently_reserved=permanent_key_reservation,
        all_storage_writers_fenced=all_storage_writers_fenced)
    return {
        "decision": decision,
        "delete_permitted": False,
        "requires": ("permanent no-reuse key reservation, all Storage writer fencing, "
                     "verified Storage CAS delete, fresh DB reconciliation and operator approval"),
    }

"""Safety architecture for orphan cleanup without an atomic Storage delete.

Keep orphan records in the durable queue and retain the bytes. Reclaim
requires a reviewed version-fenced Storage operation or an offline,
exclusive-write maintenance window. This is not a deletion worker.
"""

def orphan_recovery_decision(*, post_exists: bool, version_pinned: bool,
                             atomic_delete_supported: bool,
                             exclusive_write_lock: bool = False) -> str:
    if post_exists:
        return "retain_posted"
    if not version_pinned:
        return "quarantine_no_version"
    if not atomic_delete_supported:
        return "quarantine_no_atomic_delete"
    if not exclusive_write_lock:
        return "quarantine_no_exclusive_lock"
    # This function never deletes; the backend must still prove fencing.
    return "eligible_for_review_only"

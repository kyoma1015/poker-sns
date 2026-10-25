"""Isolated-only durable cleanup worker against local Supabase PostgREST.

Fails closed when Storage has no conditional delete by object version.
Never deletes a posted video or an unpinned object. No production use.
"""
from uuid import UUID, uuid4
from .isolated_db_adapter import _rpc

def run_one(base_url: str, service_key: str, inspect_object, delete_if_version):
    worker = str(uuid4())
    if base_url != "http://127.0.0.1:56321" or not service_key:
        raise PermissionError("isolated cleanup requires fixed loopback API and service key")
    if not callable(inspect_object) or not callable(delete_if_version):
        raise PermissionError("isolated cleanup requires explicit safe Storage adapters")
    jobs = _rpc(base_url, service_key, "video_qa_claim_cleanup",
                {"p_worker": worker, "p_lease_seconds": 120})
    if not jobs:
        return "idle"
    job = jobs[0]
    job_id, owner, path = job["id"], job["owner_id"], job["object_path"]
    success = False
    reason = "unverified"
    try:
        if str(UUID(owner)) != owner:
            raise ValueError("noncanonical owner")
        path_owner, filename = path.split("/")
        stem, dot, extension = filename.rpartition(".")
        if path_owner != owner or not dot or extension not in ("mp4", "webm") or str(UUID(stem)) != stem:
            raise ValueError("invalid queued object path")
        posted = _rpc(base_url, service_key, "video_qa_reconcile",
                      {"p_owner": owner, "p_path": path})
        if posted:
            success, reason = True, "referenced by post: retain"
        else:
            # A version token must be bound to the queued object at enqueue
            # time, not obtained here: inspecting only now permits ABA races.
            expected = job.get("expected_object_version")
            if not isinstance(expected, str) or not expected.strip():
                reason = "no pinned object version: cannot safely delete"
            else:
                current = inspect_object(owner, path)
                if current is None:
                    # A missing object is not durable proof of cleanup:
                    # a stale job can race with a re-upload at the same path.
                    # Retain the retryable job unless a tombstone/fence
                    # proves the key can never be reused.
                    reason = "object absent but immutable tombstone unproven: retry"
                elif current != expected:
                    reason = "object version changed: retain"
                elif delete_if_version(owner, path, expected):
                    success, reason = True, "conditional deletion succeeded"
                else:
                    reason = "conditional delete unsupported or rejected"
    except Exception:
        reason = "worker operation failed; retry"
    finished = _rpc(base_url, service_key, "video_qa_finish_cleanup",
                    {"p_id": job_id, "p_worker": worker,
                     "p_success": success, "p_reason": reason})
    if not finished:
        raise RuntimeError("cleanup lease lost; cannot acknowledge")
    return "complete" if success else "retry"

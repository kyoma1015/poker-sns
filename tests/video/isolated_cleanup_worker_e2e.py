"""Real isolated PostgREST queue claim/reconcile/ack E2E.

This deliberately does not perform Storage deletion: no atomic conditional
delete/version fencing API has been established.
"""
import os
from pathlib import Path
from datetime import datetime, timezone
from tests.video.isolated_cleanup_worker import run_one

def main():
    env = {}
    for line in Path(os.environ["VIDEO_QA_ENV"]).read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            env[key] = value.strip('"\'')
    service = env.get("SERVICE_ROLE_KEY")
    if not service:
        raise RuntimeError("isolated service key missing")
    # The SQL contract QA rolls back its seeded posted queue row. Do not
    # assume it persists into this independently executed HTTP test.
    from unittest.mock import patch
    from tests.video import isolated_cleanup_worker as worker_module
    owner = "10000000-0000-0000-0000-000000000001"
    good_path = owner + "/30000000-0000-0000-0000-000000000001.mp4"
    cases = (
        ("cross_owner", "20000000-0000-0000-0000-000000000002/" + good_path.split("/", 1)[1], "pinned-v1"),
        ("invalid_path", owner + "/not-a-uuid.mp4", "pinned-v1"),
        ("unpinned_version", good_path, None),
    )
    for name, path, version in cases:
        calls = []
        job = {"id": "60000000-0000-0000-0000-000000000001",
               "owner_id": owner, "object_path": path,
               "expected_object_version": version}
        def isolated_rpc(base, key, fn, payload):
            calls.append(fn)
            if fn == "video_qa_claim_cleanup":
                return [job]
            if fn == "video_qa_reconcile":
                return None
            if fn == "video_qa_finish_cleanup":
                assert payload["p_success"] is False
                return True
            raise AssertionError("unexpected RPC " + fn)
        def no_storage(*args):
            raise AssertionError("unsafe Storage operation: " + name)
        with patch.object(worker_module, "_rpc", side_effect=isolated_rpc):
            outcome = run_one("http://127.0.0.1:56321", service,
                              no_storage, no_storage)
        assert outcome == "retry", (name, outcome)
        assert calls == (["video_qa_claim_cleanup", "video_qa_finish_cleanup"]
                         if name != "unpinned_version" else
                         ["video_qa_claim_cleanup", "video_qa_reconcile", "video_qa_finish_cleanup"]), (name, calls)
        print("PASS: isolated cleanup worker fail-closed " + name)

    # Real PostgREST queue E2E: insert malformed jobs in isolated DB and
    # verify the worker retries without invoking either Storage callback.
    from uuid import uuid4
    from urllib.request import Request, urlopen
    import json
    # This local-stack test runs after finalize E2E, which can leave queued
    # posted-object jobs. Clear only the ephemeral isolated QA queue so that
    # each worker claim is deterministically the job inserted below.
    clear = Request("http://127.0.0.1:56321/rest/v1/video_cleanup_queue?id=gt.0",
                    headers={"apikey": service, "Authorization": "Bearer " + service},
                    method="DELETE")
    with urlopen(clear, timeout=10) as response:
        assert response.status in (200, 204)
    print("PASS: isolated cleanup E2E queue reset")
    for name, path, version in cases:
        payload = {"owner_id": owner, "object_path": owner + "/" + str(uuid4()) + ".mp4" if name == "unpinned_version" else path,
                   "expected_object_version": version}
        request = Request("http://127.0.0.1:56321/rest/v1/video_cleanup_queue",
                          data=json.dumps(payload).encode(),
                          headers={"apikey": service, "Authorization": "Bearer " + service,
                                   "Content-Type": "application/json", "Prefer": "return=representation"},
                          method="POST")
        with urlopen(request, timeout=10) as response:
            rows = json.load(response)
        assert len(rows) == 1, (name, rows)
        # Earlier failed jobs have backoff; this new row is claimable.
        storage_calls = []
        def deny_storage(*args):
            storage_calls.append(args)
            raise AssertionError("Storage must not be accessed for " + name)
        result = run_one("http://127.0.0.1:56321", service,
                         deny_storage, deny_storage)
        assert result == "retry", (name, result)
        assert not storage_calls, (name, storage_calls)
        # Confirm the real queue acknowledged this exact job as a failed
        # attempt, with durable retry metadata and no completed deletion.
        job_id = rows[0]["id"]
        status_request = Request(
            "http://127.0.0.1:56321/rest/v1/video_cleanup_queue?id=eq." + str(job_id)
            + "&select=id,attempts,last_error,next_attempt_at,completed_at,lease_owner,lease_until",
            headers={"apikey": service, "Authorization": "Bearer " + service})
        with urlopen(status_request, timeout=10) as response:
            persisted = json.load(response)
        assert len(persisted) == 1, (name, persisted)
        saved = persisted[0]
        assert saved["id"] == job_id and saved["attempts"] == 1, (name, saved)
        assert saved["completed_at"] is None and saved["last_error"], (name, saved)
        assert saved["lease_owner"] is None and saved["lease_until"] is None, (name, saved)
        retry_at = datetime.fromisoformat(saved["next_attempt_at"].replace("Z", "+00:00"))
        assert retry_at > datetime.now(timezone.utc), (name, saved)
        print("PASS: real isolated PostgREST cleanup queue rejects " + name + " without Storage access; retry persisted")

if __name__ == "__main__":
    main()

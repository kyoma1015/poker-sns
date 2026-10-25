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

    # A posted object must be retained even when a cleanup job is queued.
    # Reconciliation wins over inspection and deletion, including a pinned job.
    retained_calls = []
    retained_job = {"id": 98765, "owner_id": owner, "object_path": good_path,
                    "expected_object_version": "pinned-posted-v1"}
    def posted_rpc(base, key, fn, payload):
        retained_calls.append(fn)
        if fn == "video_qa_claim_cleanup":
            return [retained_job]
        if fn == "video_qa_reconcile":
            return "40000000-0000-0000-0000-000000000001"
        if fn == "video_qa_finish_cleanup":
            assert payload["p_success"] is True
            assert "retain" in payload["p_reason"]
            return True
        raise AssertionError("unexpected RPC " + fn)
    def posted_no_storage(*args):
        raise AssertionError("posted object must not reach Storage")
    with patch.object(worker_module, "_rpc", side_effect=posted_rpc):
        retained = run_one("http://127.0.0.1:56321", service,
                           posted_no_storage, posted_no_storage)
    assert retained == "complete", retained
    assert retained_calls == ["video_qa_claim_cleanup",
                              "video_qa_reconcile", "video_qa_finish_cleanup"], retained_calls
    print("PASS: isolated cleanup retains posted video without Storage inspection or deletion")

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
    # Real DB reconciliation must protect a committed post even when a
    # cleanup job has a pinned version. No Storage inspection or deletion.
    from tests.video.isolated_db_adapter import publish_post, reconcile_post
    posted_owner = owner
    posted_path = posted_owner + "/" + str(uuid4()) + ".mp4"
    # Isolated-only fixture: create an Auth user to satisfy posts.user_id FK.
    anon = env.get("ANON_KEY") or env.get("PUBLISHABLE_KEY")
    if not anon:
        raise RuntimeError("isolated anon key missing")
    signup = Request(
        "http://127.0.0.1:56321/auth/v1/signup",
        data=json.dumps({"email": "video-cleanup-" + str(uuid4()) + "@example.invalid",
                         "password": "video-isolated-test-Password1!"}).encode(),
        headers={"apikey": anon, "Content-Type": "application/json"},
        method="POST")
    with urlopen(signup, timeout=20) as response:
        signup_result = json.load(response)
    posted_owner = signup_result["user"]["id"]
    posted_path = posted_owner + "/" + str(uuid4()) + ".mp4"
    published_id = publish_post("http://127.0.0.1:56321", service,
                                posted_owner, posted_path, "cleanup retention E2E")
    assert reconcile_post("http://127.0.0.1:56321", service,
                          posted_owner, posted_path) == published_id
    posted_queue = Request(
        "http://127.0.0.1:56321/rest/v1/video_cleanup_queue",
        data=json.dumps({"owner_id": posted_owner, "object_path": posted_path,
                         "expected_object_version": "pinned-posted-v1"}).encode(),
        headers={"apikey": service, "Authorization": "Bearer " + service,
                 "Content-Type": "application/json", "Prefer": "return=representation"},
        method="POST")
    with urlopen(posted_queue, timeout=10) as response:
        posted_job = json.load(response)[0]
    posted_storage_calls = []
    def forbidden_posted_storage(*args):
        posted_storage_calls.append(args)
        raise AssertionError("committed post must not touch Storage")
    assert run_one("http://127.0.0.1:56321", service,
                   forbidden_posted_storage, forbidden_posted_storage) == "complete"
    assert not posted_storage_calls, posted_storage_calls
    posted_status = Request(
        "http://127.0.0.1:56321/rest/v1/video_cleanup_queue?id=eq."
        + str(posted_job["id"])
        + "&select=attempts,last_error,completed_at,lease_owner,lease_until",
        headers={"apikey": service, "Authorization": "Bearer " + service})
    with urlopen(posted_status, timeout=10) as response:
        saved_posted = json.load(response)[0]
    assert saved_posted["completed_at"] is not None, saved_posted
    assert saved_posted["lease_owner"] is None and saved_posted["lease_until"] is None
    assert saved_posted["attempts"] == 1 and "retain" in saved_posted["last_error"]
    assert reconcile_post("http://127.0.0.1:56321", service,
                          posted_owner, posted_path) == published_id
    print("PASS: real isolated committed post retained; queue acknowledged; zero Storage access")

    # A pinned but already-absent object must retry until a durable tombstone exists.
    # This exercises the real claim/reconcile/finish RPC chain and lease release.
    absent_path = owner + "/" + str(uuid4()) + ".mp4"
    absent_payload = {"owner_id": owner, "object_path": absent_path,
                      "expected_object_version": "pinned-absent-v1"}
    absent_request = Request(
        "http://127.0.0.1:56321/rest/v1/video_cleanup_queue",
        data=json.dumps(absent_payload).encode(),
        headers={"apikey": service, "Authorization": "Bearer " + service,
                 "Content-Type": "application/json", "Prefer": "return=representation"},
        method="POST")
    with urlopen(absent_request, timeout=10) as response:
        absent_job = json.load(response)[0]
    inspected = []
    def absent_inspection(checked_owner, checked_path):
        inspected.append((checked_owner, checked_path))
        return None
    def deny_delete(*args):
        raise AssertionError("absent object must never be deleted")
    absent_result = run_one("http://127.0.0.1:56321", service,
                            absent_inspection, deny_delete)
    assert absent_result == "retry", absent_result
    assert inspected == [(owner, absent_path)], inspected
    absent_status = Request(
        "http://127.0.0.1:56321/rest/v1/video_cleanup_queue?id=eq."
        + str(absent_job["id"])
        + "&select=id,attempts,last_error,completed_at,lease_owner,lease_until",
        headers={"apikey": service, "Authorization": "Bearer " + service})
    with urlopen(absent_status, timeout=10) as response:
        saved_absent = json.load(response)[0]
    assert saved_absent["completed_at"] is None, saved_absent
    assert saved_absent["lease_owner"] is None and saved_absent["lease_until"] is None, saved_absent
    assert saved_absent["attempts"] == 1 and "tombstone" in saved_absent["last_error"], saved_absent
    print("PASS: real isolated cleanup queue retries pinned absent object without durable tombstone")

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

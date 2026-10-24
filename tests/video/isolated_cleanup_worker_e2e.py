"""Real isolated PostgREST queue claim/reconcile/ack E2E.

This deliberately does not perform Storage deletion: no atomic conditional
delete/version fencing API has been established.
"""
import os
from pathlib import Path
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
    def forbidden_delete(*args):
        raise AssertionError("referenced video must never be deleted")
    result = run_one("http://127.0.0.1:56321", service,
                     lambda *args: "unknown", forbidden_delete)
    if result != "complete":
        raise AssertionError("referenced queued object not acknowledged")
    print("PASS: isolated durable cleanup worker retained posted object")
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


if __name__ == "__main__":
    main()

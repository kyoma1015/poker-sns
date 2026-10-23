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

if __name__ == "__main__":
    main()

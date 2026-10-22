# A — selective main-based controller integration (2026-10-22)

Status: CONDITIONAL PASS for isolated import/safety tests; not activated or merged.
Base: main `7da31f078624178dbddf8f1edf59eb8d0bf782b7`.
Source: PR69 `4d30c7ac0d08104f9d159987e38c823ef7c3b419`.

Main lacked these controller/queue modules. Before copying, importing them exited1
with ModuleNotFoundError. This is deterministic reuse of reviewed existing code,
not a rerun of the original implemented task or a claim of new worker execution.
Only the10 required source/config/test files were copied as exact Git blobs;
the provenance manifest records size/SHA256 for every imported file. Imported
protected3 acceptance files are unchanged, and imported27 tests still pass.

## Lock review and isolated acceptance

Leases initialization acquires the existing bounded cross-process setup guard
before connection/WAL/schema creation, closes a failed initialization connection,
and releases the guard on exit. Leases construction releases that guard before
claim starts its SQLite transaction. claim commits before run_task/prepare later
acquire the Git preparation guard, so these paths do not nest those locks.
finish constructs Leases first and retains the existing transaction/replay guards.
No retry/expiry/claim/path/hash policy was modified by this integration.

setup_lock retains its30-second acquisition deadline; SQLite retains its existing
10-second busy timeout. A non-cooperating external holder may still cause a
bounded failure; this is not an unlimited retry or blanket concurrency guarantee.
New temp-only tests confirm lock timeout followed by reopen preserves completed
job state and no replay; abnormal process exit releases the OS guard for the next
initializer. Tests never use the retained private shared state.

Executed:
- `python -B -m unittest discover -s tests/worker_acceptance -v`:27PASS.
- `python -B tests/automation/test_code_worker.py`:22PASS.
- `python -B tests/automation/test_development_queue.py`:15PASS.
- `python -B tests/automation/test_controller_integration.py`:2PASS.
- Imported-file SHA256 verification:10/10 exact; git diff --check PASS.

Evidence: `docs/qa/a-controller-integration-20261022/`. The dedicated5-minute CI
has read-only contents permission, checkout credentials disabled, no dependency
installation, no scheduler, no worker/model dispatch, and owned fixtures only.
Queue config remains validation_only/code_worker_configured=false. No SQLite,
token, private receipt, credentials, real backup or customer data is imported.

No poll/SQL/UI source changed; no merge/cherry-pick, main update, push, PR creation,
production/DB/Vercel/network operation or scheduler activation was performed by
this integration worker. Root owns publication, CI observation and approval.
Passing these fixtures does not prove unattended runtime operation or authorize
production release. npm/build/lint are not applicable to this Python-only import.

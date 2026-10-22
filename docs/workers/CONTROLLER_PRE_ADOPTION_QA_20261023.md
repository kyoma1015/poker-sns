# Issue22 controller pre-adoption integration QA

Manual execution began 2026-10-22T17:35:48UTC (2026-10-23 02:35:48JST).
Base: PR107 6d2f4834d3a06abb61058fcebca952f360ec0f45. This is a stacked Draft candidate, not a main/controller adoption.

## Existing inheritance, not duplicate implementation

Pinned GitHub heads and exact Git object hashes are in docs/qa/controller-integration-20261023/source-matrix.json. PR38/69/74 have byte-identical code_worker.py. PR106/107 have a newer complete code_worker.py but the same Leases initializer AST. PR107 continuation_recovery.py is byte-identical to PR106 and adds the opt-in InvocationGuard. PR38/69/74 do not contain that guard/publication schema. Therefore PR38 CI alone cannot prove the complete PR107 controller composition.

PR38 1ad98e82750fc3056efcc1d2b8da8f44e7b611f2 CI39822888471 SUCCESS; PR103 24ccde5490225d52b9e8328d86fa425bca59a664 component CI39822671500 SUCCESS; PR107 CI39796232980 SUCCESS. All remain Draft/unmerged. Main remains781f038415503ece850c25a26e72ef67dee9c8a1.

## Reproduced new failure and minimal source fix

Immutable input e1c1f638e01d78a4a79fbda80b95fb923f74835a adds nine integration tests without changing source: eight PASS, one FAIL. A deterministic injected controller DDL OperationalError occurs after Leases successfully initializes. Continuation.__init__ propagates the exception without closing its owned connection. This is a separate failure path from PR69's Leases constructor fix. No descriptor/task is replayed and no existing protection is weakened.

Source fix16fd9d43e97b1ce12e2823a424b7883a8128782e wraps only continuation schema initialization in try/except BaseException, closes the owned lease connection, and rethrows. It does not change DDL order, lock scope, schema, CAS, guard, limits or task semantics. The test verifies the connection is unusable after failure and restart preserves the seeded completed task and schema recovery. Some DDL may already be durable; this is resumable initialization, not an atomic schema migration claim.

## Executed results

- New integration suite9PASS; repeated ten times,90/90PASS,0FAIL. Each round includes eight separate processes racing DELETE-to-WAL initialization and first controller DDL, and four separate processes competing on the same publication revision. The ten rounds exercise80 mixed initializers and40 CAS contenders; one CAS winner per round.
- Existing protected acceptance85PASS; worker22PASS; queue15PASS. All ten original acceptance files remain byte-identical to pinned PR107, with SHA256 proof. No test deletions or relaxed assertions.
- Publication SQL failure rolls back metadata/revision, clears the transaction and allows the next valid update.
- Same run ID cannot enter concurrently or replay after restart. Completed task cannot be reclaimed.
- Stop arriving after reservation but before the entry check prevents the body. The consumed run ID is retained, not refunded/replayed.
- Stop during execution is cooperative: the next guard.check() prevents the next step. Arbitrary code between checks is not forcibly interrupted; this is not a preemptive worker cancellation proof.
- SIGKILL releases the OS invocation lock while retaining the finite run reservation. Unknown running task remains running and blocks a new invocation, even if its lease appears expired; no takeover is performed.
- SIGKILL during an uncommitted publication update preserves the previous committed checkpoint and allows a subsequent CAS update.

Leases setup_lock covers connect/WAL/job-table initialization; the subsequent continuation DDL remains outside that setup lock and uses SQLite busy_timeout10000ms/autocommit locking. The bounded mixed-process experiment passes; it is not proof against every external writer, filesystem or long lock holder. No wider serialization change is justified by a reproduced failure in this test.

Dedicated isolated CI runs85+22+15 existing tests and ten rounds of9 integration tests, with contents:read, five-minute timeout, no schedule and no credentials persisted. Python-only changes: application npm/build/browser tests are not applicable and are not claimed.

## Retained-state and checkpoint boundary

The retained45 records remain43implemented/2blocked/running0; original4 hashes match. Existing blocked C-chip-oracle-v1 and D-doubleclick-v1 are neither changed nor retried. All retained DB access uses mode=ro; no Continuation/Leases/guard is instantiated against it. New QA/source work is tracked in Git only, not registered in that DB. Logical job digest and checkpoint SHA256 are in retained-state-observation.json. Checkpoint digest remains b8afdc9feb93d142f723c41850d5806c0efc5917cafe6cd2324255cdab2555c0.

The checkpoint's CI references describe already-successful source-bearing commits, while latest PR heads may include later documentation commits. Both the saved source CI and current PR-head CI were checked; historical entries are not rewritten to imply current controller adoption. This QA does not reconcile every historical task's publication into the unadopted PR106 schema.

## Provider observation remains UNKNOWN

Formal peek still exposes disabled probe6ada2596d5148191be6c9dbf73ec2d34, unchanged DTSTART20261022T160246Z/HOURLY COUNT2, next_run_time null. last_run_time16:57:54.154987UTC precedes the calculated second schedule17:02:46UTC by291.845013seconds. last_run/latest_result are null, delivery_status unknown. No new runID/start/end/log/history evidence is available; timezone conversion does not establish the cause. Null next_run_time cannot prove normal COUNT2 completion. No reservation is modified, resumed or created. These manual source/fixture tests are not autonomous-start proof.

## Remaining gates and next step

Review the new stacked Draft against exact PR107, require its isolated CI and source/test hashes, then separately review controller adoption. Do not switch the retained controller, merge main or enable a scheduler without explicit approval. Independent coldstart, provider runID/history, actual worker cancellation/check placement, retained-state restoration and bounded unattended execution remain unproven. Poll release remains NO-GO. No production Supabase/Vercel/paid-service operations.

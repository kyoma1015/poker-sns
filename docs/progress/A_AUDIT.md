# A | F03 selected integration candidate
Date: 2026-10-20 JST
Status: CONDITIONAL PASS; release BLOCKED.

Base main: f8890b6ec11d30676c55dc7dc8801f1da8549d28.
Candidate source: cb31df805c7d64e8986f23e6af718ea1cd02655e.
Only the five planned application files are ported: App, Timeline, PostDetail, PlayerProfile and createVerifiedNotification. The diff preserves the other main features; no audit-branch routing, sharing or poll features are imported.
PostDetail obtains savedComment.id before verified comment notification. Notification errors do not undo saved comments.
Acceptance: no direct notification inserts at these entry points; no retry on authorization/validation; transient errors retry the same event; ignored abort still completes within budget.
Tests: F03_BASELINE_ROOT=/workspace/poker-sns node tests/f03-notification.test.mjs failed on main's direct INSERT as expected. node tests/f03-notification.test.mjs: 11 PASS with fake RPC and virtual clock.
npm ci blocked locally by proxy EPERM; npm run build (tsc missing) and npm run lint (oxlint missing) blocked. PR CI performs locked install, unit, build and lint independently.
No DB connection, SQL or production actions. The verified RPC/schema is a prerequisite; legacy direct INSERT permission is deliberately unchanged.
Remaining: isolated DB event-provenance/idempotency/legacy-client tests BLOCKED (no isolated DB configured). Browser QA, production tabs and rollback plan still required. Do not merge/revoke INSERT based on unit success.


## Integrated verification update (2026-10-20)
Integrated in B → D → A → SNS order. Local network permission resolved the previous registry blocker. npm ci, full unit regression, build and lint now run successfully on the integrated source; see INTEGRATION_VERIFICATION_20261020.md and docs/qa/integration-20261020/. Earlier blocked statements above describe the previous lane task. No production DB verification or release approval is implied.


## Controller pre-adoption QA — 2026-10-23 JST
PR107 pinned6d2f4834d3a06abb61058fcebca952f360ec0f45 composition tested on owned temporary SQLite only. New controller-DDL connection cleanup defect reproduced9tests/1FAIL, minimal sourcefix16fd9d43e97b1ce12e2823a424b7883a8128782e; after9PASS, ten rounds90PASS, existing85/worker22/queue15PASS. All original acceptance bytes preserved. Retained45records43implemented/2blocked/running0 untouched (mode=ro), no new lease or controller adoption. Evidence docs/workers/CONTROLLER_PRE_ADOPTION_QA_20261023.md and docs/qa/controller-integration-20261023/. Independent provider startup remainsUNKNOWN; no reservations/main/production/billing changes. This is manual QA/source work, not unattended operation.


## Worker continuity and bounded recovery QA — 2026-10-23 JST
Stacked on PR1119068971e8571e3bd162b8173a42d735be0c969b9. Two new fixed failures: timeout leaves a SIGTERM-ignoring descendant after leader exit; cleanup failure masks original DDL error. Input77f1c96c581594f660038096cfef107759749f12:8tests/2FAIL, source87232734b26e98d8e7a10a437394708bd1ec6743:8PASS/10rounds80PASS; old85/worker22/queue15/controller9PASS. Real OS processes + actual controller/worker APIs + real local Git commits, but synthetic executors/catalog/receipts explicitly real_ai_implementation:false. Demonstrates retained uncommitted work→verified one retry→commit→next reviewed fixture task under2-run cap; no run reset. Lost coordinator while worker lives remains fail-closed pending positive liveness confirmation. Evidence docs/workers/WORKER_CONTINUITY_QA_20261023.md and docs/qa/worker-recovery-20261023/. Retained45jobs43implemented/2blocked/running0 and checkpoint unchanged, ro-only. No main/controller/scheduler/production activation. Independent provider startUNKNOWN, pollNO-GO.


## PR112 IO/cleanup continuation —2026-10-23 JST
New phased fixed baselines5/4FAIL +1/1FAIL +4/1FAIL +5/4FAIL, then15PASS/ten rounds150PASS; existing85/22/15/9/8/1PASS. Code_worker only: bounded nonblocking stdin/cleanup, explicitUNKNOWN running/context retention across expiry, process observation denial not confused with exit, observed escaped descendants refuse continuation. No retained45state changes/new jobs/leases; no controller/main/scheduler adoption. Software wait budgets are not a hard all-kernel wall-clock guarantee; snapshots do not prove all descendants. Formal-host boundary callback wiring and independent automatic launch remain unproved. Evidence docs/workers/WORKER_IO_BOUNDS_20261023.md and docs/qa/worker-io-bounds-20261023/. PollNO-GO.

## Trusted host stop boundary — 2026-10-23
PR113-based opt-in InvocationGuard.call_host preparation: pre/post stop/deadline, positive liveness, preserve-before-return. Eleven missing-capability cases1FAIL/10ERROR ->11PASS, ten rounds110PASS; old85/22/15/9/8/1/5PASS. Temporary callbacks/DB only, no actual formalhost or scheduler connection. Source-only finite guard reuse, retained45jobs untouched. See docs/workers/HOST_CALL_BOUNDARY_20261023.md. Hard watchdog/containment and real cancellation remain gates; pollNO-GO.

## Corrupt running evidence fail-closed — 2026-10-23
PR117 follow-up: exact-parent corrected8test/37failure observations →8PASS; activation race4FAIL→4PASS, supporting2CAS/resumePASS, ten rounds140PASS. Existing156PASS. All running malformed/legacy/missing evidence preserved and blocks all lanes; new typed not_started leases plus token/status/expiry activationCAS preserve normal expiry/retry while refusing old-owner dispatch. No heldstate mutation or host activation. Evidence docs/workers/CORRUPT_EVIDENCE_20261023.md and docs/qa/corrupt-evidence-20261023/. Independent read-only review conditional, formalhost/watchdog incomplete, pollNO-GO.

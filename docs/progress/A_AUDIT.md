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

## New source continuation — 2026-10-22
A80 finite lease inputs and A85 finite setup waits: fixed35/39 +worker22/queue15 PASS, dedicated CI SUCCESS. See [ledger](../workers/ISSUE22_AUTONOMOUS_SOURCE_20261022.md). Existing source/original4state/BLOCKED history retained; no production/main/paid action.

2026-10-22 Draft96 adds bounded durable discovery metadata to the existing controller:49fixed+22worker+15queuePASS/CI39767309432. No task promotion or live state/controller adoption. Source a3186ef6a5da4c3489aa2e7947fdea2b00395c31; see ISSUE22_DISCOVERY_CONTINUATION_20261022.md for limits.

2026-10-22 Draft102 finite invocation clocks58+22+15PASS/CI39784286230; Draft104 bounded read-only discovery CLI67+22+15PASS/CI39785322289. Live controller/state schema unchanged. Exact source/restart: ISSUE22_SELECTED_REUSE_20261022.md.

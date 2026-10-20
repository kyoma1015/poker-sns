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

## Continuous A security milestone — 2026-10-20
Baseline PR #13: 3ca87764e988cac588fef915d48823702a1a3326. Acceptance: production audit high/critical zero; preserve API behavior and locked reproducible install; no DB changes.
The vulnerable undici 5.28.4 comes from @vercel/node's pinned development dependency and is also included as OpenAI's optional peer. Even @vercel/node 25.0.0 still pins 5.28.4; audit fix dry-run changed nothing. Pinned override undici=6.29.1 removes the vulnerable @fastify/busboy dependency and satisfies OpenAI's >=5 <9 peer interval. This is an explicit major override of Vercel's pinned transitive dependency, not a claim that upstream updated it.
Production audit: high 2 → 0; critical 0 → 0. Full audit still finds dev-only high 8 / moderate 1 (Vercel tooling chain, including braces with no fixed release in the audit report). These require separate toolchain work; do not claim all dependencies vulnerability-free.
Runtime reachability inspection: application API uses native global fetch and OpenAI SDK; @vercel/node imports in application sources are type-only. Vercel local dev-server uses undici Headers/request. Three offline tests exercise those APIs, fetch JSON and mocked OpenAI responses. This is compatibility evidence, not a running Vercel deployment or exploitability proof for every advisory.
Tests: npm ci, full unit regression, npm run build/lint, production audit, and existing mocked browser QA. Evidence: docs/qa/continuous-a-20261020/. CI now supports integration-base PRs and enforces production high/critical audit.
Main merge/deploy/production DB changes were not performed. A security-only main-based PR is prepared separately so this fix does not import PR #13's unverified DB features. Rollback: revert the security dependency commit and reinstall from lock; this would reintroduce known vulnerable dependencies, so block release until remediated rather than silently shipping the rollback.

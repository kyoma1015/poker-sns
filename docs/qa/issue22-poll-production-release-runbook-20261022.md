# Poker ID / Issue #22 — poll-only production release runbook (review-only)
Date: 2026-10-22 UTC. Baseline main: `7da31f078624178dbddf8f1edf59eb8d0bf782b7` (PR #71 merged).
**Status: NO-GO. This document is NOT permission to run production SQL.** Owner approval, maintenance window, verified recoverability, and a separate release review are mandatory. No production Supabase writes, Vercel changes, paid upgrades, or Draft PR merges are authorized.

## 0. Evidence and immutable scope
- Production read-only observations: `public.post_interactive` has 8 polls and 4 historical questions, 0 NULL `is_anonymous`. Preserve *all* rows, related responses, posts and notifications, not merely counts.
- Legacy cron: job 1 `poker_id_poll_closed_notifications` active, command `select public.dispatch_poll_closed_notifications();`. Snapshot found 0 running interactive jobs; **recheck at cutover**.
- Production `create_interactive_post_v4` and `get_interactive_results_v4` are SECURITY DEFINER; authenticated EXECUTE present, anon EXECUTE absent. Proposed forward SQL changes exposed wrappers to invoker semantics; **do not claim already applied**.
- Candidate RLS restrictive policies `poll_raw_identity_guard_v1`, `poll_metadata_visibility_v1`, `poll_closed_forgery_guard_v1` are absent in production. Verify effective policy composition, grants, PostgREST behavior and all overload signatures before release.
- PR #71 CI run 39720684508 succeeded on synthetic isolated Postgres/PostgREST QA, including emergency disable stopping *both* cron names. This does not establish production recoverability.
- Existing `tests/polls/verify_backup_restore.sh` restores only 3 fixture tables (post_interactive, responses, notifications), excluding dependent application data, full FK relationships, role/extension configuration and Storage object bytes. This is NOT a production restore rehearsal.

## 1. HARD GATE: backup and recovery (before ANY write)
1. Owner identifies project plan and current backups in Supabase Dashboard > Database > Backups, timestamps/retention, availability and restore permissions. No paid add-on or restore-to-new-paid-project without separate authorization.
2. Obtain a **private**, restorable logical export via approved read-only database export mechanism, including dependent `posts`, `post_interactive`, `post_interactive_responses`, `notifications`, `profiles`, `user_blocks`, related schemas/functions/policies/triggers/grants, extensions/cron definitions, and referenced objects as required by dependencies. Audit FK graph and choose full compatible dump if subset is not closed. Exclude credentials/tokens from GitHub and public CI artifacts. Storage API objects are not included in a database-only backup; handle separately if relevant.
3. Record source project, export timestamp, database/server version, dump format/tool version, SHA-256 of encrypted private artifact, restore owner/location, TTL, and evidence retention. Do not publish raw votes, identity mappings or notification data.
4. Restore into an **authorized isolated destination** with no production callbacks/cron/notifications enabled, and verify restore exit status, schema/functions/grants, FK consistency, data hashes and row counts; explicitly assert 8 polls, 4 questions, and all original response/notification records with stable identifiers. Evidence should use counts and digests, never sensitive raw rows.
5. Document the recovery decision tree: emergency feature disable is **not** database rollback; full database restore may overwrite newer production data and require downtime. Specify RPO/RTO and owner approval. If an isolated restore cannot be demonstrated safely and without cost, remain NO-GO.

## 2. Read-only cutover preflight (rerun immediately before owner-approved maintenance)
- Query `cron.job` for **all** commands and names matching poll/interactive, not just known names; record job IDs and active flags.
- Query `cron.job_run_details` for running poll/interactive commands; zero is a point-in-time observation, not a persistent guarantee.
- Snapshot `pg_proc` signatures, SECURITY DEFINER flags and EXECUTE privileges for all public interactive RPC overloads; enumerate `pg_policies` on notifications/post_interactive/post_interactive_responses, role grants and table counts.
- Check `notifications` existing `poll_closed` events, `event_key` uniqueness and close-receipt state for dedupe. Ensure migrations do not replay legacy notifications.
- Capture current user-facing behavior and explicit maintenance window, rollback contacts, and SQL file SHA hashes.

## 3. Reviewed write sequence (future OWNER execution only; NOT executed by this task)
1. Announce maintenance/write freeze; keep a verified backup/restore checkpoint. Confirm no unexpected interactive cron or worker exists.
2. Stop **legacy** `poker_id_poll_closed_notifications` using reviewed owner-authorized change; wait for in-flight execution to drain. Confirm both `cron.job` and `cron.job_run_details` state; do not race the next minute boundary. Record exact state. Do not run the new scheduler alongside legacy.
3. Apply reviewed `sql/poll_only/forward_candidate.sql` with expected prerequisites, signatures, idempotence, timeouts and failure atomicity. **Do not apply older feature-branch migrations**; preserve historical question rows and poll votes. If a transaction fails, stop and investigate before retry.
4. Before scheduling, verify wrapper RPC signatures and SECURITY INVOKER status, anonymous vs named results, user blocks, notification anti-forgery, RLS policies, no direct raw response identities, old data hashes/counts, and no duplicate close notifications, using a reviewed three-role verification protocol. Do not create test data in production without separate consent.
5. Only after old cron is absent and all in-flight executions are drained, run `sql/poll_only/schedule_candidate.sql`. Its existing-cron and in-flight checks intentionally fail closed; **do not weaken/bypass them**. Confirm exactly one `pokerid-poll-close-v1` scheduled with `select poll_private.close_due_polls();` and no legacy job.
6. Observe safe idempotence and notification delivery, plus 8 original polls/4 original questions and complete identity/privacy invariants. Public enablement and Vercel are separate approvals; neither is performed here.

## 4. Emergency stop and controlled recovery
- Owner-approved `sql/poll_only/disable_candidate.sql` (post PR #71) unschedules **both** known cron job names, revokes client RPC EXECUTE, preserves historical posts/votes/questions/notifications/receipts and guards. Already running cron is **not** cancelled by unschedule; wait for drain. This is a feature-disable, **not** a destructive schema rollback.
- Re-enable only after incident diagnosis, exact grants/policies revalidated and isolated QA repeated; do not automatically restart cron. Repeat legacy job absence/in-flight zero check, then separately authorize schedule.
- Never publish backups, sensitive responses, access tokens, or restore credentials in this repository.

## 5. Explicit blockers / release sign-off
- [ ] Private backup is actually obtained and SHA-verified; safe isolated full-dependency restore evidenced.
- [ ] Release owner signs off on the old-cron unschedule/drain and maintenance window.
- [ ] Live RPC overload/privilege and RLS privacy behavior checked against candidate signatures and approved three-role protocol.
- [ ] Migration SQL dry-run / rehearsal on production-equivalent restored fixture succeeds with 8+4 historical preservation.
- [ ] Exact one-scheduler cutover, close dedupe, emergency disable/re-enable drill evidenced.
- [ ] Separate production-write and Vercel/publication authorizations recorded.

## 6. Other Issue #22 work: isolation boundaries
- PR #69 (Draft) touches only `scripts/code_worker.py` as a PR patch, but its inherited branch diverges from main (ahead35/behind116). Review process-lock adoption and controller lease/startup behavior against **current main**; never merge the entire branch without explicit approval.
- PR #66 (Draft) touches only `gto/native/settlement.py` as a PR patch; inherited branch diverges (ahead22/behind116), with unrelated poll/SNS conflicts. Prepare a fresh source-only candidate against current main; verify fixed fixtures, native bridge, GTO regressions and exact source hashes. No claim of G11 ABI/checkpoint compatibility or strategy convergence.
- PR #70 remains Draft and toy-game-only. B immutable 350-question evidence, D expert labels and G11 source/checkpoint remain blocked.
- Any future source-only candidate must get independent isolated CI and owner review; this documentation PR changes **no runtime code**.

References: `sql/poll_only/forward_candidate.sql`, `sql/poll_only/schedule_candidate.sql`, `sql/poll_only/disable_candidate.sql`, `tests/polls/run_isolated.sh`, `tests/polls/verify_backup_restore.sh`, https://supabase.com/docs/guides/platform/backups.

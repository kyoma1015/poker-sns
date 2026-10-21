# Poker ID | Poll-only production release gate (read-only audit 2026-10-22)

**Decision: NO-GO until owner explicitly authorizes production SQL and Vercel release.** This document records a plan, not production execution. Never use synthetic QA writes in production.

## Verified against live Supabase (read-only)

- post_interactive: 6 `poll`, 4 historical `question`; responses: 3 votes and 3 historical answers.
- Existing `poll_closed` notifications: 6; duplicate (post_id,user_id) notification pairs: 0.
- Legacy cron: `poker_id_poll_closed_notifications`, `* * * * *`, active, calling `public.dispatch_poll_closed_notifications()`.
- Existing dispatcher is SECURITY DEFINER, returns integer, inserts legacy `poll_closed` notifications with no event_key and no `poll_private.close_receipts`.
- `poll_private` is not deployed. RPC signatures: create -> uuid, submit -> void, legacy/v4 results -> exact TABLE signatures verified by PR49 isolated tests.
- Notification INSERT RLS permits sender != recipient; SELECT/UPDATE own recipient. No notification uniqueness constraint except id PK.
- Existing post_interactive and response constraints, question rejection trigger, relevant RLS and posts quote trigger inspected.

## Further verified preflight: 2026-10-22 01:13 JST

- **Production deployment is already live but behind main**: Vercel alias `poker-sns-vert.vercel.app` resolves to READY production deployment `dpl_95ynBzuABKa2DUgofwpQix8fBBRB`, Git SHA `e83113d1d1f92a6a421e687390748530ebb88d27`. Current main after PR50 is `c6a3573d86f82570891d36d9473b0532f79dbdc0`. A separate READY preview deployment `dpl_EPEeyTvd6mz5TFtrUCxGH2U3Xn9r` for branch PR49 SHA `2891c3ba8547708e28f4b07218265ad7db282646` does **not** update the production alias. No Vercel actions taken.
- **Backup blocker is material**: Supabase organization subscription is `free`. Supabase official backup documentation does not guarantee automatic daily backups on Free. There is no backup-list/verification operation exposed by the connected Supabase integration. Therefore **do not treat a restorable production backup as available**. Before any production SQL, take an authorized independent logical backup (`supabase db dump` or `pg_dump`, including schema/roles/data where appropriate), store it securely off-host, and prove restoration in a separate isolated environment. Do not place customer data, dump bytes, DB passwords or credentials in GitHub.
- **Confirmed project**: Supabase `poker-id` project is ACTIVE_HEALTHY, PostgreSQL 17.11, region ap-northeast-1. Read-only migration list shows prior notification-cron and legacy-question guard changes; no new poll-private migration.
- **Advisors**: Supabase security advisors contain warnings in unrelated modules (e.g. anonymously executable SECURITY DEFINER RPCs, mutable function search_path); these findings require their own security review and were not altered in the poll-only audit.
- **Publication remains NO-GO**: production database unchanged, old cron still running; backend migration, actual GoTrue authenticated QA, independent restorable backup, synchronized Vercel release and release approval outstanding.

## Blocking findings and mitigation

1. **Historical close-notice replay (fixed in candidate; still awaiting new CI):** the original `poll_private.close_due_polls()` only consulted close receipts and would re-notify already closed polls. The candidate must also exclude polls with an existing `notifications(type='poll_closed',post_id,user_id)` row. The disposable QA harness seeds an old notification and verifies two close worker executions do not duplicate it.
2. **Scheduler overlap:** the legacy worker neither locks poll rows nor coordinates with new close receipts; neither table currently provides a unique `(post_id,user_id,type)` constraint. Do not run both schedulers simultaneously. New `schedule_candidate.sql` deliberately rejects the live cron until it is removed. An already running legacy job may continue after unscheduling; wait and verify no executing legacy job remains before enabling the replacement. If run-state cannot be verified, STOP.
3. **Release is not reversible by a schema rollback alone:** `disable_candidate.sql` disables feature RPCs and new job while retaining votes, historical questions/answers, security guards and receipts. It does not restore old RPC definitions or UI. Keep verified backups and a documented forward-fix/restore plan.
4. **Production parity remains incomplete:** GoTrue sign-in/refresh, actual authenticated mobile-to-live-backend flows, production storage/RLS beyond this feature, and Vercel deployment have not been tested. PR49 mock browser + PostgREST JWT fixture are not substitutes.
5. **Old `poll_closed` notifications have no unique index**: without maintenance-window quiescence, only application-level safeguards are insufficient to prove cross-worker concurrency safety.

## Go / no-go operational sequence (future, requires explicit authorization)

1. Freeze feature rollout. Confirm deployed Vercel SHA, main SHA, branch and migration checksum. Obtain and verify a restore-capable Supabase backup/PITR and capture *fresh* preflight inventory: table columns/checks/PK/FK, function signatures and ACLs, RLS, triggers, cron jobs and execution state. Record counts for 6 polls, 4 questions, 3 votes, 3 answers, all existing notifications; use dynamically rechecked counts, not assumed fixed release-day numbers.
2. Confirm the approved SQL files exactly match CI-passed SHA. Prove the old notification job is healthy and no duplicate `poll_closed` pairs exist. Run migration and release checks against a restored staging snapshot with *real schema*, no real-user writes.
3. **Core-only DB migration first:** apply `sql/poll_only/core_without_notifications_candidate.sql` in its own transaction. Check RPC results/anonymous privacy, legacy data count preservation, grants/RLS, and no unexpected cron/trigger. Existing legacy cron remains active. Roll out no UI yet. If any check fails, STOP and use reviewed disable/restore plan.
4. In an approved maintenance window, disable new poll creation UI; ensure old poll close worker execution is quiescent. Apply `sql/poll_only/forward_candidate.sql` (includes notification guard and new worker) only after snapshot checks and review. Validate old notices remain unchanged before any schedule change.
5. **Single-job handoff:** unschedule `poker_id_poll_closed_notifications`; verify no in-flight executions; verify live cron catalog has no other poll worker. Only then apply the separately reviewed `sql/poll_only/schedule_candidate.sql`, which creates `pokerid-poll-close-v1`. No interval may have two running close workers; if uncertain leave new worker unscheduled and STOP.
6. Verify one and only one close notice per eligible poll, no replay of historical notices, `event_key` correctness for new notices, no raw anonymous voter identity via REST, zero new question rows, stable historical counts, existing like/comment/follow notifications, cron success/error history, and idempotency of close retries.
7. Only after DB acceptance, deploy approved frontend via Vercel. Perform authorized real GoTrue login on test-only accounts, create poll 2–4 options, anonymous/named modes, cast votes, test results before/after close, verify notification and no answer/question box, mobile nav, errors and rollback. Do not interact with other people's data.
8. Release owner records GO with timestamp and evidence. If no GO, leave Vercel unchanged.

## Stop criteria and response

- RPC return mismatch, unknown policy/trigger/column, privacy regression, count loss, two close jobs, duplicated notice, failed close retry, inability to establish backup or cron quiescence, or client regression -> STOP.
- Before enabling new cron, preserve or recover legacy cron if necessary; never reactivate both jobs. If new cron is live and fails, stop it first; run `disable_candidate.sql` only after reviewing its broad feature-disable consequences, and restore legacy worker only with clear single-job status. Do not delete posts, answers, notifications, or close receipts as an emergency rollback.
- DB rollback/feature-disable and Vercel frontend rollback are **separate** decisions. Never treat the disable script as restoring original function definitions.

## Evidence boundaries

- PR49 isolated CI (reported passed by Work): https://github.com/kyoma1015/poker-sns/actions/runs/39630047622
- Current production data and catalog inventory queried in read-only mode on 2026-10-22.
- The historical notification replay fix requires a **new** green isolated CI before even considering GO.

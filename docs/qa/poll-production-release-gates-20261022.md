# Poker ID | Poll-only production release gate (2026-10-22)

Status: **NO-GO** until each gate below has objective evidence. This is a runbook, not an authorization to change live data.

## Verified live state (read-only)
- GitHub `main`: `9cbb59f4b6428ed87705ee46abe1eac2676bdc0b` (PR #45).
- Vercel production alias `poker-sns-vert.vercel.app`: READY deployment `dpl_H19t4neABHa8disTw9F6M9Z2UURb` from `5cbea02ba942286afe3c7fdb6b0fa7d07c3dc178` (PR #43), **not** main.
- Supabase production: 6 poll metadata rows, 4 preserved historical question rows. `reject_new_question_interactive` trigger is installed. `poll_private.close_receipts` and `poll_private.close_due_polls()` are absent.
- Legacy cron `poker_id_poll_closed_notifications` is ACTIVE every minute and executes `select public.dispatch_poll_closed_notifications();`. Its function inserts `poll_closed` notifications for closed polls using `not exists` and `on conflict do nothing`. **Do not run two schedulers concurrently**.
- Isolated CI for PR #45 (run 39625020072) passed. Its synthetic fixtures are NOT a production schema clone.
- Production has all 6 polls closed. Therefore live create/vote/open-close end-to-end cannot be validated without explicitly authorized new test records.

## Release sequence — no destructive shortcuts
1. **Freeze and backup**: obtain verified PITR/restore checkpoint, record production schema, grants, policies, functions, indexes, triggers, `cron.job` (including command), existing `poll_closed` uniqueness/deduplication behavior and migration history. Do not export private user rows into GitHub.
2. **Parity gate**: compare production catalog with `sql/poll_only/core_without_notifications_candidate.sql` and `forward_candidate.sql`, especially existing 4 creation RPCs, results v2/v3/v4, response RPCs, `notifications` triggers, `post_interactive_responses` raw access and historical privacy. Review that the restrictive response SELECT policy will not break unrelated existing clients. Ensure the question-blocking trigger remains effective after all migrations.
3. **Staging rehearsal**: on a disposable isolated clone with representative schema and *synthetic* data, run the exact candidate in intended order, verify repeated apply, anonymous/named votes and results, blocked users, question creation denied through every old RPC and direct INSERT, retained historical question/answer rows, no notification forgery, close deduplication, RLS and rollback. Obtain a green CI artifact and written parity sign-off. Do not use production user credentials/data for QA.
4. **Core-only deployment**: only after parity approval, consider `core_without_notifications_candidate.sql` first, with live catalog preflight and migration-history recording. **Do not run `forward_candidate.sql` on top of core by assumption**, because it also defines close worker/notification objects. Explicitly review SQL overlap and lock/timeout/rollback behavior. Retain the legacy scheduler at this phase; confirm no duplicate notification writes and no regression to existing data.
5. **Vercel**: after DB RPC compatibility is confirmed, deploy the reviewed GitHub `main` SHA to a preview first. Verify login, poll composer, no question UI, vote/result privacy and mobile layout with synthetic test accounts. Then promote to production and verify the alias resolves to the **exact expected SHA**. Do not assume a merged PR auto-deployed.
6. **Scheduler cutover** (separate maintenance window): inspect and reconcile old dispatcher with new receipt-based worker; document notification uniqueness, owner approval and rollback. Stop old job and start new job atomically only after tested backup/rehearsal. `sql/poll_only/schedule_candidate.sql` intentionally fails while old cron exists; never bypass this gate or run both jobs.
7. **Post-release verification**: read-only catalog + deployment SHA + RLS/grants + data-count invariants; execute only approved synthetic-user write QA; compare notification counts and error logs. If any gate fails, stop and use a separately rehearsed rollback; `disable_candidate.sql` is NOT full schema restoration.

## Current blockers / release decision
- Vercel production is behind main by PR #44/#45.
- New poll core/close worker is not in live DB.
- No proof that the isolated fixture exactly matches live policies/ACL/notification schema.
- Existing live cron conflicts with the new schedule candidate.
- Existing polls are all closed; no authorized live synthetic write QA has been performed.

**Decision: NO-GO for automatic production migration, scheduler change or promotion.** Preserve existing user data and the installed question-blocking trigger.

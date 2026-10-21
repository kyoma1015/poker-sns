# Poker ID poll close cron: production cutover gate

Status: **NO-GO**. This is a review checklist, not an instruction to execute a migration automatically.

## Verified

- Isolated compatibility and rollback QA: https://github.com/kyoma1015/poker-sns/actions/runs/39618410797 (success).
- Live PostgreSQL catalog contains a SECURITY DEFINER `public.dispatch_poll_closed_notifications()` function.
- Live cron named `poker_id_poll_closed_notifications` runs the dispatcher each minute.
- Candidate `sql/poll_only/schedule_candidate.sql` rejects a second poll-related cron while a legacy job exists.
- No production SQL, cron change, or deployment has been performed by this audit.

## Owner-only evidence required before GO

1. Review the **complete current dispatcher body** and any functions it calls. Determine whether it sends `poll_closed` notifications, modifies poll state, or uses a separate deduplication table.
2. Record the existing `cron.job` name, schedule, command, and active status, along with current notification uniqueness constraints. Keep credentials and secrets out of shared records.
3. Confirm whether old and new schedulers would compete for the same polls, and whether notification `event_key` plus close receipts make every retry idempotent.
4. Prepare a verified backup and a reversible **single-scheduler** cutover plan. Do not schedule the new job before retiring the old one in an owner-approved maintenance window.
5. Test failure/retry behavior, one close notification per poll, existing question and answer history, and notification RLS after cutover.
6. Approve release only after reviewing actual production differences from the isolated fixture, with a named owner recording GO and rollback criteria.

## Fail-safe response

If the dispatcher cannot be reviewed or any step is inconclusive, leave the existing production cron untouched, do not run `schedule_candidate.sql`, and keep the PR in draft. `disable_candidate.sql` is a feature-disable action that preserves historical records; it is not a full restoration of previous function definitions or privileges.

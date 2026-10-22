# Poker ID poll-only emergency disable and controlled reactivation

Status: **NO-GO for production** until the owner has verified production backup and isolated restore, approved a maintenance window, and explicitly approved each production change. This is a candidate/test plan only.

## Live read-only audit (2026-10-22)
- Aggregate poll count: **8**, historical questions **4**, poll votes **3**, historical answers **3**, existing poll-closed notifications **6** (counts change as users interact; never freeze these as migration expectations).
- Current production RPCs `create_interactive_post*`, `submit_interactive_response*`, `get_interactive_results` and `get_interactive_results_v4`: authenticated EXECUTE enabled; anonymous EXECUTE not allowed.
- Historical `get_interactive_results_v2/v3`: authenticated EXECUTE disabled; legacy close dispatcher: authenticated EXECUTE disabled.
- Current `post_interactive`, `post_interactive_responses` and `notifications` have only existing permissive SELECT/INSERT/UPDATE policies. The candidate's restrictive poll policies are **not yet deployed**; this is NOT proof of the new privacy protections in production.
- `poll_private` is not deployed yet. Existing production remains untouched.

## Disable (future, only after explicit release authorization)
- `sql/poll_only/disable_candidate.sql` unschedules **only** `pokerid-poll-close-v1`, revokes exposed public poll RPCs and `poll_private` helper grants from anon/authenticated, and reloads PostgREST metadata. It preserves posts, votes, historical questions, answers, close receipts, RLS, triggers and all notifications.
- It is a **feature shutdown**, not a restoration of the former functions or the application client. It does not automatically restore the legacy worker. Do not run to “test” against live production.
- Capture a fresh private backup, snapshot and cron state first. If any old cron exists or appears in in-flight pg_cron history, do not activate a competing scheduler.

## Re-enable (future, independently authorized)
1. Confirm original incident resolved; obtain fresh backup/isolated restore proof, approved SQL SHAs, current schema/RPC/RLS diff, and rollback owner authorization.
2. With new scheduler **off**, execute `sql/poll_only/core_without_notifications_candidate.sql` in its independent transaction (repairs creation, voting and result definitions/grants); then `sql/poll_only/forward_candidate.sql` in its independent transaction (restores helper grants and notification worker/guard). The second candidate must never itself start cron.
3. Before scheduling, verify authenticated can execute only approved public creation/vote/results RPCs, anon cannot, v2/v3 old result RPCs remain denied, and `poll_private.close_due_polls()` is not callable by app roles; validate restrictive RLS policies. Ensure previous user data counts and old notifications are unchanged.
4. Assess legacy cron versus new cron in `cron.job` and the still-running historical executions in `cron.job_run_details`. `sql/poll_only/schedule_candidate.sql` rejects an old cron or in-flight previous close job. The owner must manually complete a quiescent single-job handoff, with no competing workers.
5. Only after DB acceptance, explicitly approve the matching frontend release and real GoTrue QA. Otherwise leave Vercel untouched.

## Isolated regression evidence

`tests/polls/run_isolated.sh` now runs **disable twice → core + forward twice → assert authenticated/private grants, denied old RPCs and close worker, retained historical question/answer/notification, and no auto-created cron** in a throwaway Supabase PostgreSQL fixture. This test is not evidence that an actual production restore exists.

**No production SQL, cron job, data row or Vercel deployment was changed in this work.**

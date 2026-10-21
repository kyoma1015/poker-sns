# Poll-only production catalog audit — 2026-10-21 (READ ONLY)

## Scope and safety
Compared **live** Supabase project `poker-id` public schema catalog (read-only SQL) with `sql/poll_only/forward_candidate.sql` from PR #31, head `df1c05a3f01d85cae1a8324b39951bcad3b83ab3`. No DDL, DML, RPC invocation, migration, deployment, or changes to existing data were performed.

## Verified blockers

1. **Creation RPC signature mismatch**: production `public.create_interactive_post_v3(text,text,text[],integer,boolean)` has **five** parameters. Candidate preflight allowlist expects `create_interactive_post_v3:text,text,text[],integer,boolean,text` (**six**). Candidate will fail its fail-closed catalog gate on this production schema. Production `v4` has six arguments.
2. **Historical results RPCs**: production has `get_interactive_results_v2(uuid[])` and `get_interactive_results_v3(uuid[])`. Candidate rejects any results RPC except unversioned and v4; preflight will fail. Investigate function definitions, EXECUTE grants and caller compatibility before any retirement or replacement. Current authenticated EXECUTE: unversioned true, v2 false, v3 false, v4 true.
3. **Question creation remains possible via authenticated historical RPCs**: production `create_interactive_post`, `_v2`, `_v3`, `_v4` are SECURITY DEFINER and each permits `p_kind='question'`. All four have authenticated EXECUTE. Client-side poll-only scope does not by itself close this path. Candidate intends poll-only wrappers but its preflight cannot currently reach them. Preserve historical question posts, answers and thread data.
4. **Old write RPCs remain callable**: authenticated EXECUTE on `submit_interactive_response` and `_v2`; inspect old-data compatibility and ensure post-deployment wrappers reject new question responses if product scope requires, while preserving existing historical data.
5. **RLS is enabled** for `post_interactive`, `post_interactive_responses`, `question_thread_messages`; visible permissive policies are `interactive_read` (metadata) and `interactive_responses_own_read` (responses). Presence of RLS alone is not proof of privacy.
6. **Existing extensions**: `pg_cron` and `pg_stat_statements` are installed in production. Isolated Docker fixture differences do not imply production extension setup is missing.
7. **Existing rows**: `post_interactive` 10, `post_interactive_responses` 6, `question_thread_messages` 6 at read time. These counts are not evidence of privacy mode or permission correctness. No row content read.
8. **Migration history** contains interactive privacy/notification migrations including `named_poll_voters_and_visibility`, `poll_closed_notification_cron_once`, and `revoke_legacy_interactive_results_anonymity_exposure`. Compare function versions and cron definitions, not just table columns.

## Required implementation before production SQL approval
- Modify candidate catalog allowlist based on **actual five-argument v3**, but first establish full exact signatures, function bodies, dependencies, and owner-approved handling of v2/v3 result functions. Do not simply remove fail-closed checks.
- Explicitly deny **all** question creation routes, including old authenticated RPC signatures, while retaining historic rows and any approved historic read-only UI.
- Check notification column/trigger/cron compatibility, grants, all RLS policies (permissive/restrictive), table defaults, constraints, indexes, existing `poll_closed` receipts, and legacy API calls.
- Rerun isolated PostgREST/GoTrue-equivalent QA against a schema faithfully exported from production, plus read-only preflight. Revalidate privacy across author/voter/third-party identities and direct RPCs.
- Produce reversible migration and backup/restore plan. **Do not apply to production** until explicit owner approval and deploy access.

## Additional security review
Supabase security advisor reported warnings for exposed SECURITY DEFINER RPCs, including TDA and diagnosis functions. These are not automatically exploitable; investigate intentional grants separately, avoiding unrelated production modifications.

## Status
**BLOCKED for production deployment.** This audit is a grounded catalog comparison and handoff; it is not a migration, QA pass, or authorization to deploy.

## Additional live catalog verification (read-only)
- Existing cron job: `poker_id_poll_closed_notifications`, schedule `* * * * *`, command `select public.dispatch_poll_closed_notifications();`. The candidate creates a **different** private close function and separate scheduler. **Do not enable the new schedule alongside the old one** until the old dispatcher semantics, receipts, deduplication, and migration plan are audited. The existing cron must not be silently dropped.
- Notifications table has `event_key`, `id`, `user_id`, `actor_id`, `type`, `post_id`, `read_at`, `created_at`. Existing permissive policies allow authenticated INSERT, own SELECT and own read UPDATE; candidate's restrictive `poll_closed` guard must be verified against real client insert workflows.
- `post_interactive` CHECK constraints permit both `poll` and historical `question` rows; this is necessary for historical preservation. Block **new question creation in RPC**, not by changing the existing CHECK to forbid historical question rows.
- `post_interactive_responses` PK is `(post_id,user_id)` and FK references `auth.users`; candidate isolated fixture must faithfully model these constraints.
- Existing `question_response_policy_valid` CHECK permits `anonymous_only`, `named_only`, `respondent_choice`; leave historical values intact.
- A request to inspect the old dispatcher definition was blocked by the connected tool safety gate; no assumption about its behavior is made. **Cron compatibility remains BLOCKED.**

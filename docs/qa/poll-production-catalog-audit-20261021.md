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

## Implementation update — 2026-10-21
- Candidate SQL on this branch now replaces `create_interactive_post_v3(text,text,text[],integer,boolean)` **using its exact production signature** (commit `a31175a45af1823f378b8b8929b36b5c6b204808`), forwarding to poll-only v4 with NULL question policy. This fixes the earlier six-argument overload hazard. This change is **not deployed**.
- Candidate results v2/v3 are wrapped through poll-only v4, preserving historical return shapes and leaving their client EXECUTE grants revoked. Verify all consumers and question history requirements before approval.
- The existing production cron `poker_id_poll_closed_notifications` still makes `sql/poll_only/schedule_candidate.sql` **fail closed**. Do not remove its conflict gate without verifying the legacy dispatcher and an owner-approved single-scheduler migration plan.
- A full isolated database test of this modified branch has **not** been executed; previous 56 passing tests belong to a different commit and must not be presented as verification of these changes.

## Isolated acceptance update and cron migration gate
- GitHub Actions run 39615811756 completed all workflow steps successfully on commit a0f771b, including isolated Postgres/PostgREST tests, client regression, build, lint, and mobile browser mock QA. Evidence: https://github.com/kyoma1015/poker-sns/actions/runs/39615811756/artifacts/12351479996 . This verifies the fixture, **not** full production catalog parity.
- Commit 8bbb10b adds a disposable-DB test for the production-named cron collision. The candidate scheduler must reject a second poll scheduler without altering either job; this additional test is pending CI verification.
- Production cutover remains **NO-GO**. A reviewer must obtain and inspect the old dispatcher definition, its notification event-key deduplication, transaction boundaries, and interaction with the new close receipts. The connector safety gate prevented retrieval; do not bypass it or assume compatibility.
- Before owner-approved production change: take a verified backup, record cron.job schedule/command/active and grants, verify that only one close scheduler will be active after migration, confirm historical question rows and notification history remain intact, and document restoration steps. Avoid enabling both schedulers concurrently.
- Rollback is a feature-disable operation, not a data rollback: preserve all historical posts, votes, close receipts, RLS privacy guards and notification history. Confirm that the rollback revoke list covers all public interactive results RPC versions.

## Latest isolated verification (2026-10-21)
- Run [39616733751](https://github.com/kyoma1015/poker-sns/actions/runs/39616733751) completed successfully at commit `0f5cfc5`'s predecessor `0f5cfc5` **not included**; specifically it ran commit `0f5cfc5586d71329b5d98d56b0c211b616bbbbb6`. The cron-collision guard was exercised in disposable PostgreSQL; evidence artifact [12352358858](https://github.com/kyoma1015/poker-sns/actions/runs/39616733751/artifacts/12352358858).
- Run [39617562199](https://github.com/kyoma1015/poker-sns/actions/runs/39617562199) tests the latest `0fffdac198f1fcd5280c71ee7fa7750107b27622`, including twice-run feature-disable rollback and preservation checks. Its job logs show artifact upload [12353377044](https://github.com/kyoma1015/poker-sns/actions/runs/39617562199/artifacts/12353377044), with final GitHub run conclusion still pending at audit time.
- `disable_candidate.sql` now revokes `get_interactive_results_v2` and `get_interactive_results_v3` as well as other interactive RPCs. The rollback is deliberately fail-closed and retains data, receipts and restrictive RLS.
- **NO-GO remains** for live cutover until existing production dispatcher is reviewed and single-cron cutover approved; isolated fixture success is not proof of full production parity.

## Production-shaped legacy RPC fixture acceptance
- GitHub Actions [39618410797](https://github.com/kyoma1015/poker-sns/actions/runs/39618410797) completed **successfully** on commit `7e3024c8d52c78cf983e9bf12e57be3dfd6191f2`.
- Isolated fixture now creates pre-migration production-compatible `create_interactive_post_v2/v3` and `get_interactive_results_v2/v3` RPCs, including five-argument v3 creation and distinct six-/seven-column result shapes.
- Disposable PostgreSQL asserts migration does not create a six-argument v3 overload and removes SECURITY DEFINER/client EXECUTE exposure from historical v2/v3 results. Existing cron collision and feature-disable tests also run in this workflow.
- This confirms **fixture compatibility**, not exact live PostgreSQL function bodies, grants, table constraints, or deployed production behavior. Existing live `poker_id_poll_closed_notifications` dispatcher remains unreviewed; **production cutover stays NO-GO**.

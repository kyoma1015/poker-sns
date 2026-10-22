# Poker ID poll-only release gate — 2026-10-22

**Decision: NO-GO.** Documentation and synthetic CI success are not production recovery proof or permission to deploy. This is a read-only GitHub audit; no live Supabase connection, production dump/restore, Vercel action, payment or GTO/controller modification.

## Verified artifacts (as checked on main)

| Evidence | Result | Limits |
|---|---|---|
| PR #76 threat model | Previously merged | Risk model, not production execution |
| PR #77 `.github/workflows/poll-pg17-synthetic-restore.yml` | Synthetic PostgreSQL 17 dump/restore PASS | Synthetic fixtures only; not full dependency/Storage recovery |
| PR #78 `.github/workflows/poll-supabase-pg17-extension-compat.yml` | Supabase PostgreSQL 17.11 image exposes pg_cron 1.6.4 and supabase_vault 0.3.1 | Extension availability, not production key portability |
| PR #79 `.github/workflows/poll-cron-vault-runtime.yml` | Run 39730843915 SUCCESS: cron register/execute/unschedule, Vault synthetic encrypt/decrypt/limited role check/delete, container cleanup | Supabase image `17.11.0.004`; key is synthetic, not production; test does not establish all role grants |
| Poll isolated regression | Run 39730843876 SUCCESS; artifact 12404952148, SHA-256 `d8880eeaf7838bb9c539b3a7d197bc202ce1919df3b99cb02b03de3bc95eebc5` | Isolated tests; no live production or restored-production acceptance |

All source paths above are retained unchanged. Historical observations in `docs/qa/poll-backup-isolated-restore-feasibility-20261022.md` are snapshots, **not current production verification**.

## Release GO/NO-GO gates

| Gate | State | Evidence needed to clear |
|---|---|---|
| Synthetic PG17, cron and Vault runtime | PASS | PR #77–#79 CI logs |
| Poll regression CI | PASS | Run 39730843876 + artifact digest |
| Owner-authorized private **real production backup** | BLOCKED | Scoped backup, timestamp, SHA-256, protected storage and retention; verify coverage of auth, roles, extensions, migrations and data |
| Isolated restoration of that real backup | BLOCKED | Full dependencies, FK integrity, stable digests, row counts, roles, RLS, RPC signatures, trigger/notification checks and exit codes |
| Vault production-key restoration/decryption compatibility | BLOCKED | Approved secure key custody and decryption proof in isolated restore; never print key or decrypted data |
| Storage object bytes and external dependencies | BLOCKED | Metadata-to-byte reconciliation; Auth config, Edge Functions, SMTP, secrets and integrations inventoried separately |
| Current live RPC overloads, RLS, grants, legacy data | BLOCKED | Authorized fresh catalog review, real-role acceptance, preservation of old polls and historical questions |
| Old cron retirement and in-flight drain | BLOCKED | Current job definitions, running job checks, authorized maintenance window, no duplicate schedulers |
| Release owner and independent deployment approvals | BLOCKED | Separate written production SQL, maintenance and Vercel authorization |

**GO requires every BLOCKED gate cleared with private evidence, owner sign-off and explicit new authorization.** Do not upload backups, tokens, private vote records, Vault keys or sensitive logs to GitHub.

## SQL candidate audit: exact files and hazards

1. `sql/poll_only/forward_candidate.sql`: transaction with prerequisite catalog guards, legacy privacy checks, new private close receipts and RPC/RLS changes. **Do not execute** until fresh catalog and restored-production rehearsal prove no data loss, grant regression or unexpected overload. Historical anonymity must not be guessed.
2. `sql/poll_only/core_without_notifications_candidate.sql`: reduced feature candidate, **alternative to forward**, not an extra migration to stack onto it. Validate the exact version selected on restored data.
3. `sql/poll_only/block_legacy_question_inserts_candidate.sql`: guard to reject future non-poll interactive rows; evaluate existing clients and non-poll writers before authorization. Historical rows are preserved.
4. `sql/poll_only/schedule_candidate.sql`: **important deliberate fail-closed behavior**. It rejects an existing differently named interactive cron job, including historical `poker_id_poll_closed_notifications`. It does **not** unschedule that historical job. Never run it while old cron exists, and do not “fix” this guard by bypassing it. The separate owner-approved old-job retirement/drain must precede this script.
5. `sql/poll_only/disable_candidate.sql`: emergency feature-disable; revokes listed client RPCs and unschedules both known cron names while preserving posts, votes, receipts and RLS. Already running jobs must still drain. **Not a destructive schema rollback and not a guarantee of full re-enable.**

## Proposed application sequence — future owner-only, NOT executed

0. Obtain explicit authorization, maintenance window, independent reviewer and a secure offline destination; freeze competing schema and scheduler changes.
1. Obtain scoped private backup and independently verify its hash. Separately capture Storage **bytes** and external configuration inventory under appropriate access controls.
2. Restore to a disconnected, production-equivalent PostgreSQL 17 environment with side effects disabled; establish complete source/destination parity, extension/Vault-key compatibility, RLS/RPC grants, legacy data and notification dedupe.
3. Rehearse the **chosen one** of `forward_candidate.sql` or `core_without_notifications_candidate.sql` on that restore. Rehearse optional legacy-question guard if authorized. Run tests as anon, authenticated, owner, and least-privileged roles.
4. Rehearse and document exact cron transition on restore: inspect old cron command and active runs; retire old job only after explicit approval; wait for in-flight jobs to drain; ensure zero overlapping close schedulers; run `schedule_candidate.sql`; verify exactly one new job, one close notification and idempotent retry.
5. Rehearse emergency `disable_candidate.sql`; verify old and new jobs absent, RPCs denied, existing records preserved and running jobs drained. Re-enable **only** by separate reviewed grants/policies and scheduler procedure, not an automatic inverse of disable.
6. Recheck live production catalog and backups immediately before any real write. **STOP here under the current authorization.** Production execution and Vercel publication require separate user approval after all gates pass.

## Incident response / safe rollback

- Freeze new writes and publication. If a security or integrity incident occurs, obtain owner authorization to execute `disable_candidate.sql` and check running cron drain; preserve records and forensic evidence.
- Confirm affected client RPCs are denied and cron jobs are absent. Do not DROP poll tables, restore old permissive grants or assume unschedule cancels a running job.
- If data repair is needed, escalate to an approved private restore/reconciliation procedure based on the verified backup; do not overwrite production blindly.
- Re-enable only after root-cause analysis, exact RLS/grants revalidation, fresh isolated QA, cron uniqueness verification and independent explicit approval.

## Next actionable work without production access

- Add isolated synthetic **old-cron transition/drain and emergency-disable/re-enable** assertions using test-only fixtures, or extend role-boundary tests without keys in logs.
- Review release checklist against fresh GitHub main changes before any approval.
- Do not equate synthetic cron/Vault success with production backup or recoverability.

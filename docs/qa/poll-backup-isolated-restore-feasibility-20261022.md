# Poll-only backup and isolated restore feasibility — 2026-10-22 UTC

**NO-GO / READ-ONLY EVIDENCE ONLY.** No production writes, dump, restore, deployment, payment or Codex GTO/controller changes occurred. Builds on `docs/qa/issue22-poll-production-release-runbook-20261022.md` (PR #72, merged as `d8b3687f058227ce8a779d463262d4e2b6fad536`).

## Current source-backed facts
- Supabase organization subscription returned `plan=free`, `tier=tier_free`; project `poker-id` ACTIVE_HEALTHY, PostgreSQL 17.11, region ap-northeast-1.
- Production read-only SQL: extensions pg_cron 1.6.4, pg_stat_statements 1.11, pgcrypto 1.3, plpgsql 1.0, supabase_vault 0.3.1, uuid-ossp 1.1; `storage.objects` metadata rows **7**; `supabase_migrations.schema_migrations` **19** rows.
- Previous catalog observations: 8 polls, 4 historical questions, no NULL anonymity, legacy cron active, no `poll_private` schema. These are point-in-time observations, not a release approval.

## No-extra-subscription candidate
Supabase official backup guidance says Pro/Team/Enterprise projects receive automatic daily backups; Free projects should export via Supabase CLI `db dump`. PITR is a paid add-on, therefore excluded. The CLI logical dump plus **local Docker** isolated restoration is a potential zero-additional-cloud-fee workflow; not yet performed or validated on the owner's machine. Cloud project duplication is not assumed free.

Supabase official platform-to-self-hosted guide gives separate role, schema, and data exports:
```sh
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f roles.sql --role-only
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f schema.sql
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f data.sql --use-copy --data-only
```
These are **examples for future owner review**, NOT executed commands. Verify installed CLI syntax using `supabase db dump --help`, and protect credentials from terminal history, logs and GitHub. CLI filters reserved roles/internal schemas; these files are not proof of complete platform recovery.

## Recovery verification gates
1. Owner reviews connection method, encryption, backup scope, authorized private destination and RPO/RTO; record timestamp and SHA-256 without leaking private data.
2. Verify local Docker/CLI capacity and compatible PostgreSQL 17 + extension behavior (especially pg_cron and Vault). Do not assume a default PostgreSQL 15 image can fully reproduce production 17.
3. Restore only into isolated local destination with external cron, mail, webhooks and outbound side effects disabled; retain restore logs/exit codes.
4. Compare source and destination table counts, referential integrity, stable digests, RLS/GRANT, RPC signatures, triggers, extensions, auth and notification dedupe; include responses and historical questions, not just 8/4 counts.
5. Inspect the **7 Storage object metadata records** to identify separately needed **object bytes**. Database backups do not include Storage API file bytes. Also inventory Edge Functions, external Auth settings, secrets and SMTP; don't publish them.
6. On restored fixture, rehearse old-cron unschedule/drain, `forward_candidate.sql`, real-role privacy/RLS/RPC/notification tests, `schedule_candidate.sql`, and `disable_candidate.sql`. Record evidence. No production writes without separate explicit authorization.

## Outstanding blockers
- No actual private dump, cryptographic digest, restore exit code or parity evidence.
- No demonstrated local PostgreSQL 17/pg_cron/Vault compatibility.
- No verified Storage file recovery path, complete dependency inventory or real-role acceptance on restored production-equivalent data.
- No production old-cron cutover approval, maintenance window or production-write authorization.

**Decision: NO-GO.** A plausible no-extra-cloud-fee workflow is identified, not executed.

Sources:
- https://supabase.com/docs/guides/platform/backups
- https://supabase.com/docs/guides/self-hosting/restore-from-platform
- https://supabase.com/docs/reference/cli/supabase-db-dump

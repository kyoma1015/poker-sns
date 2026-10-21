# Poker ID — production read-only backup execution readiness (2026-10-22)

**Release gate: NO-GO.** This is a local-operator preparation; nothing in this PR takes an actual production dump or changes production Supabase/Vercel.

## What was verified
- Supabase official [Database Backups](https://supabase.com/docs/guides/platform/backups) says Free-tier projects should periodically use the Supabase CLI `db dump` and retain copies off-site. Automated daily backups are for Pro/Team/Enterprise.
- Official [restore guide](https://supabase.com/docs/guides/self-hosting/restore-from-platform) gives three exports (roles, schema, data) and a **separate self-hosted** restoration, with restore validation. Supabase-aware CLI export excludes Supabase internals which make raw `pg_dump` difficult to restore.
- Connected Supabase integration provides SQL queries and project metadata, but **no safe binary backup export or isolated file storage**. The available execution container has neither `supabase` CLI nor `pg_dump` nor Docker and has no production credential mounted. The external Vercel/GitHub integrations do not provide an off-repository private dump destination.
- Existing `tests/polls/verify_backup_restore.sh` **already PASSED** with synthetic fixture and deterministic fingerprints (PR53 CI). This confirms only isolated 3-table dump/restore mechanics.

## Prepared, NOT executed against production

`scripts/poll_private_export.sh` is guarded for local VS Code terminal execution. It requires `POLL_BACKUP_DIR` (pre-created mode 0700, outside working tree) and a privately supplied `SUPABASE_DB_URL` requiring TLS, refuses GitHub Actions/CI, invokes official Supabase CLI for separate `roles.sql`, `schema.sql`, `data.sql`, and creates checksum evidence. Files are mode 0600. It does not automatically restore or transmit user data.

Use only an owner-approved, trusted machine with enough disk and Docker running. Verify `supabase db dump --help` and your connection privileges before use. Store credentials outside shell history, code, chat and logs. Do **not** run this from GitHub Actions or commit private exports. Before deploying, restore exports on a truly separate PostgreSQL/Supabase environment following the official guide and inspect full schemas, RLS, triggers, Auth metadata, and post/vote/question/notification counts. Storage object *bytes* and external auth/Edge Function settings need separate backup. An SQL dump alone does not provide complete project recovery.

## Release remains blocked by
- No **actual** production dump or private off-site storage confirmation.
- No **actual** full-schema/full-data restore in a separate environment.
- No authorized maintenance window, database migration, cron handoff or real GoTrue integration QA.
- Vercel production alias remains behind GitHub latest main (last read-only audit).

This PR only supplies the guarded local export utility, tests, and release documentation. It does not authorize or trigger any production operation.

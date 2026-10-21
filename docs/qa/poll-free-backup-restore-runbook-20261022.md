# Poker ID | Free plan backup and restore acceptance gate

**Decision: NO-GO for production SQL until a real production export is taken, stored privately, and restored successfully outside production.** This document does not authorize any production mutation or Vercel deployment.

## Officially supported approach

Supabase states that scheduled daily backups are supplied to Pro, Team and Enterprise projects, and recommends periodic CLI `db dump` exports with off-site retention for Free projects. Source: https://supabase.com/docs/guides/platform/backups

The official platform-to-self-hosted guide describes three independent export sets (roles, schema, data):
https://supabase.com/docs/guides/self-hosting/restore-from-platform

- `supabase db dump --db-url "$DATABASE_URL" -f roles.sql --role-only`
- `supabase db dump --db-url "$DATABASE_URL" -f schema.sql`
- `supabase db dump --db-url "$DATABASE_URL" -f data.sql --use-copy --data-only`

**Never execute these against production from GitHub Actions, nor commit/export the resulting files into the repository, Actions artifacts or chat.** Run them only in an authorized local/isolated host using a protected environment variable for a read-only-compatible dump connection with SSL and least privileges supported by Supabase. Connection strings and passwords are secrets. Follow the current Supabase CLI guide and verify CLI flags via `supabase db dump --help` before real execution. `supabase db dump` applies Supabase-aware filters; raw `pg_dump` is not necessarily a portable complete Supabase restore.

In addition to PostgreSQL schema and data, separately inventory Storage object bytes, project auth configuration, project secrets, Edge Functions and Cron definitions. Logical DB dump by itself does **not** back up Storage object contents. Do not claim full project recovery from SQL files alone.

## Restore proof in an isolated environment (future authorized operation)

1. Verify backup files exist, are nonempty and have privately retained checksums; use secure encrypted off-host storage (not GitHub).
2. Create a separate isolated database using an existing cost-approved environment; do not purchase or create paid Supabase projects without explicit consent.
3. Apply approved roles/schema/data restoration using the official Supabase restoration guide. Track extensions, Supabase-managed roles/objects, FK checks, grants and RLS.
4. Verify restored counts and content integrity for posts, profiles, user blocks, `post_interactive`, responses, notifications, Auth/Storage metadata as applicable, and validate RPC signatures, triggers, constraints and pg_cron definition.
5. Verify the restored legacy closed notices have no duplicates and that replacing poll cron would not replay old notices. Re-run authenticated and authorization QA with *synthetic users in the isolated copy*, without sending any notifications outside staging.
6. Record backup timestamp, revision, private checksum evidence and restore result. Do not expose user rows or tokens in CI logs.

**Current limitation:** Supabase connector offers live read-only SQL inspection, but does not expose a secure file-based export of all production rows or a backup/restore operation to an existing isolated project. No production export has been captured or restore proven in this task.

## Synthetic CI proof (safe to run unattended)

`tests/polls/verify_backup_restore.sh` runs only inside the isolated Docker PostgreSQL fixture. It dumps three synthetic interactive tables into a local temporary custom-format archive, restores table definitions and data into a separate temporary database, and compares row counts and deterministic ordered JSON checksums. The archive is deleted on exit, is not uploaded as an artifact, and contains **no production rows**. It proves the mechanics of dump and restore in the fixture, not end-to-end production restore capability.

## Release blockers

- Production-safe real backup export and off-host retention: **not done**.
- Independent restoration with production-equivalent Supabase roles/auth/cron/RLS: **not done**.
- Main-to-production Vercel drift and real GoTrue integration acceptance: **not done**.
- Release authorization for production SQL and deployment: **not provided**.

Until those are complete, maintain existing production cron and frontend; no production writes.

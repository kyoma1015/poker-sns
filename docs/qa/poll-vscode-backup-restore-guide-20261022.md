# Poker ID — VS Code backup and isolated restore operator guide

**NO-GO until a real production export and separate restoration are proven.** All commands run in a trusted **VS Code integrated terminal on the user's Mac**. Never use macOS Terminal, GitHub Actions, or upload any SQL/connection string to GitHub or chat.

## Prerequisites (the assistant cannot install these on the user's Mac)

- In the existing checked-out `poker-sns` repository, use VS Code's terminal and `git pull --ff-only` to obtain PR changes.
- Docker Desktop must already be running; Supabase CLI and `psql` are required (Homebrew is an option but install only after reviewing current official docs). Check `supabase db dump --help` and Docker availability.
- The Supabase Dashboard **Connect** panel provides a database URI for the **poker-id** project. Copy it yourself privately and include `sslmode=require`. Use a valid direct or session-pooler URI. The script never writes the URI to files, GitHub, or command history.
- Secure sufficient free disk space and encrypted offline/off-site storage. Exported database SQL includes user data; no attachment uploads.

## Minimum-step production READ-ONLY export

1. In **VS Code terminal**, from `poker-sns` repository: `git pull --ff-only`.
2. Run: `bash scripts/poll_backup_vscode.sh`.
3. At the hidden prompt paste the database connection URI from Dashboard. The script validates expected project ref and TLS, makes a local private directory under `~/PokerID-Private-Backups`, runs the repo's guarded role/schema/data export, verifies checksums and permissions, and reports only status/path. **No production DML/DDL is executed by this script**.
4. Keep the resulting SQL files private, encrypted and off-host; never commit or send them.

## Separate local restore (DO NOT attempt on production)

Follow the [official platform-to-self-hosted restore guide](https://supabase.com/docs/guides/self-hosting/restore-from-platform) and set up a fresh Supabase self-hosted instance with compatible PostgreSQL major version (production is PostgreSQL 17). Confirm that it has the expected Auth, Storage and extension baseline; there may be version incompatibilities. The helper **does not create** this environment or change other local developer databases.

Run: `bash scripts/poll_restore_local_only.sh "$HOME/PokerID-Private-Backups/<export-directory>"`.

It requires an interactive hidden **localhost** PostgreSQL URI, ensures the destination has no existing `public.post_interactive` table or Auth user records, requires the operator to type `RESTORE ISOLATED`, and uses the official single-transaction `psql` restore sequence. It rejects remote hostnames and CI. **Important:** localhost may be a proxy/tunnel; independently ensure it is not redirected to a live database. Do not run against anything but a disposable separate Supabase instance.

After successful `psql`, check Auth tables, application row counts and stable digests, migration metadata, extensions, policies, triggers, function signatures, scheduled cron jobs and anonymized business invariants. SQL restore success **alone does not prove** complete recovery. Auth configuration, Storage object bytes, secrets, Edge Functions and external settings need separately verified recovery.

## Actual status at implementation time

- No actual production dump has been taken by ChatGPT or CI.
- No real full production restore has been proven.
- GitHub testing uses only synthetic fixtures and refuses production export in CI.
- No production SQL writes, Vercel deployments or purchases are authorized.

Stop and ask for help if the CLI, Docker, database URI, separate local environment or sufficient private storage are missing. **Never paste credentials or SQL dumps into chat to troubleshoot.**

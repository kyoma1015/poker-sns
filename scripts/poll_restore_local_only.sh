#!/usr/bin/env bash
# ONLY for an already-configured, separately isolated localhost Supabase DB.
# This never connects to the production host and requires explicit operator consent.
set -euo pipefail
umask 077
fail() { printf 'RESTORE BLOCKED: %s\n' "$*" >&2; exit 2; }
[[ -z "${CI:-}" && -z "${GITHUB_ACTIONS:-}" ]] || fail 'No real backup files in CI'
[[ -t 0 && -t 1 ]] || fail 'Interactive VS Code terminal required'
[[ $# == 1 && -d "$1" && ! -L "$1" ]] || fail 'Provide private export bundle directory'
command -v psql >/dev/null 2>&1 || fail 'psql not installed; see official Supabase restore guide'
command -v node >/dev/null 2>&1 || fail 'Node.js required to verify localhost URL'
dir=$(cd "$1" && pwd -P)
bash "$(dirname "$0")/poll_verify_backup_bundle.sh" "$dir"
printf 'Restore target must be a SEPARATE, LOCAL self-hosted Supabase PostgreSQL instance.\n'
printf 'It must have matching extensions/auth/storage schemas and NO real user data.\n'
IFS= read -r -s -p 'LOCAL target PostgreSQL URI (hidden): ' restore_url
printf '\n'
[[ -n "$restore_url" ]] || fail 'Missing restore URI'
node -e 'const u=new URL(process.argv[1]);if(!["postgres:","postgresql:"].includes(u.protocol)||!["127.0.0.1","localhost","::1"].includes(u.hostname)){process.exit(2)}' "$restore_url" || fail 'Target URI host must be localhost/127.0.0.1/::1'
# Check the actual server address; an SSH tunnel/port proxy must not target prod.
[[ "$restore_url" != *ephptepeuespnxtzdqby* ]] || fail 'Source project ID prohibited in target URI'
actual_database=$(psql -X -qAt -v ON_ERROR_STOP=1 --dbname "$restore_url" -c "select current_database()" ) || fail 'Cannot connect to target'
[[ -n "$actual_database" ]] || fail 'Target DB name unavailable'
has_poll=$(psql -X -qAt -v ON_ERROR_STOP=1 --dbname "$restore_url" -c "select to_regclass('public.post_interactive') is not null" ) || fail 'Cannot inspect target'
[[ "$has_poll" == f ]] || fail 'Target already has interactive data/schema; refuse replacement'
auth_rows=$(psql -X -qAt -v ON_ERROR_STOP=1 --dbname "$restore_url" -c "select count(*) from auth.users" ) || fail 'Cannot check target Auth users'
[[ "$auth_rows" == 0 ]] || fail 'Target has Auth users; refuse restoration'
printf 'RESTORE TARGET CHECK: %s (localhost), empty interactive/Auth records.\n' "$actual_database"
printf 'Verify manually that this is a throwaway self-hosted instance, NOT a tunnel to production.\n'
IFS= read -r -p 'Type RESTORE ISOLATED to restore private user data locally: ' confirmation
[[ "$confirmation" == 'RESTORE ISOLATED' ]] || fail 'Confirmation not supplied'
# Official Supabase restore sequence; error-stop/single txn is essential.
psql -X --single-transaction --set ON_ERROR_STOP=1 --quiet \
  --file "$dir/roles.sql" --file "$dir/schema.sql" \
  --command 'SET session_replication_role = replica' \
  --file "$dir/data.sql" --dbname "$restore_url" >/dev/null || fail 'Restore failed; do not treat this backup as verified'
unset restore_url
printf 'SQL restore command succeeded locally. Check schema/roles/RLS and counts; full Supabase recoverability remains unverified until manual checks.\n'

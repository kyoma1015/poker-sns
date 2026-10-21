#!/usr/bin/env bash
# Run only in the user's trusted VS Code terminal. Does not change production.
set -euo pipefail
umask 077
fail() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
[[ -z "${CI:-}" && -z "${GITHUB_ACTIONS:-}" ]] || fail 'Do not run a production export from CI'
[[ -t 0 && -t 1 ]] || fail 'An interactive VS Code terminal is required'
command -v supabase >/dev/null 2>&1 || fail 'Supabase CLI not installed'
command -v docker >/dev/null 2>&1 || fail 'Docker CLI not installed'
docker info >/dev/null 2>&1 || fail 'Docker daemon is not running'
command -v shasum >/dev/null 2>&1 || fail 'shasum not available'
supabase db dump --help >/dev/null 2>&1 || fail 'Supabase CLI db dump unavailable'
root="$HOME/PokerID-Private-Backups"
[[ ! -L "$root" ]] || fail 'Backup root cannot be a symlink'
if [[ -e "$root" ]]; then
  [[ -d "$root" ]] || fail 'Backup root is not a directory'
  mode=$(stat -f %Lp "$root" 2>/dev/null || stat -c %a "$root" 2>/dev/null || echo unknown)
  [[ "$mode" == 700 ]] || fail 'Existing backup root must have permissions 700'
else
  mkdir -m 700 "$root" || fail 'Unable to make private backup root'
fi
printf 'Supabase project: poker-id (verify in dashboard > Connect)\n'
printf 'Paste the PostgreSQL connection URI privately into this hidden prompt.\n'
printf 'Do not paste it in chat, GitHub, command history or source files.\n'
IFS= read -r -s -p 'Supabase DB connection URI (hidden): ' db_url
printf '\n'
[[ -n "$db_url" ]] || fail 'No connection supplied'
[[ "$db_url" == postgres://* || "$db_url" == postgresql://* ]] || fail 'PostgreSQL connection URI required'
[[ "$db_url" == *sslmode=require* || "$db_url" == *sslmode=verify-full* ]] || fail 'Connection URI must include sslmode=require or sslmode=verify-full'
[[ "$db_url" == *ephptepeuespnxtzdqby* ]] || fail 'Connection must reference expected poker-id project ID'
export POLL_BACKUP_DIR="$root"
export SUPABASE_DB_URL="$db_url"
unset db_url
bash "$(dirname "$0")/poll_private_export.sh"
unset SUPABASE_DB_URL
printf '\nExport completed locally. No production DB writes or deploys performed.\n'
printf 'Private backup root: %s\n' "$root"
printf 'NEXT: restore on a separate local Supabase instance; this export is NOT a verified recovery point yet.\n'

#!/usr/bin/env bash
# Operator-run OFFLINE export; never run from GitHub Actions.
set -euo pipefail
umask 077
die() { printf 'ERROR: %s\n' "$*" >&2; exit 2; }
[[ -z "${CI:-}" && -z "${GITHUB_ACTIONS:-}" ]] || die 'Production export prohibited in CI'
[[ -n "${POLL_BACKUP_DIR:-}" ]] || die 'POLL_BACKUP_DIR missing'
[[ -n "${SUPABASE_DB_URL:-}" ]] || die 'SUPABASE_DB_URL missing'
[[ "$SUPABASE_DB_URL" == postgres://* || "$SUPABASE_DB_URL" == postgresql://* ]] || die 'Invalid connection scheme'
[[ "$SUPABASE_DB_URL" == *sslmode=require* || "$SUPABASE_DB_URL" == *sslmode=verify-full* ]] || die 'Explicit TLS is mandatory'
command -v supabase >/dev/null || die 'Install Supabase CLI; review supabase db dump --help'
[[ -d "$POLL_BACKUP_DIR" && ! -L "$POLL_BACKUP_DIR" ]] || die 'Backup directory missing or symlink'
backup_dir=$(cd "$POLL_BACKUP_DIR" && pwd -P)
[[ "$backup_dir" != "$PWD" && "$backup_dir" != "$PWD/"* ]] || die 'Do not store backups inside working tree'
[[ -z "${GITHUB_WORKSPACE:-}" || ( "$backup_dir" != "$GITHUB_WORKSPACE" && "$backup_dir" != "$GITHUB_WORKSPACE/"* ) ]] || die 'Do not store in GitHub workspace'
mode=$(stat -c %a "$backup_dir" 2>/dev/null || stat -f %Lp "$backup_dir" 2>/dev/null || echo unknown)
[[ "$mode" == 700 ]] || die 'Backup directory must have mode 700'
dest="$backup_dir/export-$(date -u +%Y%m%dT%H%M%SZ)-$$"
mkdir -m 700 "$dest"
# A failed dump must not be mistaken for a successful recovery point.
# Delete ONLY the newly-created export directory, never an existing backup.
export_complete=false
cleanup_partial() {
  if [[ "$export_complete" != true ]]; then
    rm -f -- "$dest/roles.sql" "$dest/schema.sql" "$dest/data.sql" "$dest/checksums.sha256"
    rmdir -- "$dest" 2>/dev/null || true
    echo 'Export incomplete; new partial files discarded' >&2
  fi
}
trap cleanup_partial EXIT
# Never enable xtrace; database credentials are secrets.
supabase db dump --db-url "$SUPABASE_DB_URL" -f "$dest/roles.sql" --role-only
supabase db dump --db-url "$SUPABASE_DB_URL" -f "$dest/schema.sql"
supabase db dump --db-url "$SUPABASE_DB_URL" -f "$dest/data.sql" --use-copy --data-only
for f in roles.sql schema.sql data.sql; do [[ -s "$dest/$f" ]] || die "Incomplete dump: $f"; chmod 600 "$dest/$f"; done
(cd "$dest" && shasum -a 256 roles.sql schema.sql data.sql > checksums.sha256)
chmod 600 "$dest/checksums.sha256"
bash "$(dirname "$0")/poll_verify_backup_bundle.sh" "$dest"
export_complete=true
echo 'Local private export completed. Prove a restore into an ISOLATED environment before release.'
echo 'NEVER upload these files to GitHub, Actions artifacts, or chat.'

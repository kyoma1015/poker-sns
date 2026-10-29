#!/usr/bin/env bash
# Offline PostgreSQL 17 logical-restore smoke test. Does NOT restore Supabase Storage API.
set -euo pipefail
umask 077
[[ $# -eq 1 ]] || { echo 'Usage: video_verify_isolated_db_restore.sh <decrypted-bundle-directory>' >&2; exit 2; }
root="$(cd "$1" && pwd -P)"
[[ -f "$root/database.dump" && -f "$root/database.sha256" ]] || { echo 'Missing decrypted DB dump/checksum' >&2; exit 2; }
command -v docker >/dev/null || { echo 'Docker unavailable: isolated restore NOT verified' >&2; exit 2; }
python3 "$(dirname "$0")/video_verify_backup_bundle.py" "$root"
# Neither published ports nor host networking: all operations are local.
name="video-restore-check-$$"
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run --detach --rm --network none --name "$name" -e POSTGRES_PASSWORD=local-restore-only   -v "$root/database.dump:/tmp/backup.dump:ro" postgres:17 >/dev/null
ready=false
for _ in $(seq 1 30); do
  if docker exec "$name" pg_isready -U postgres -d postgres >/dev/null 2>&1; then ready=true; break; fi
  sleep 1
done
[[ "$ready" == true ]] || { echo 'Isolated PostgreSQL unavailable' >&2; exit 2; }
# Fail closed on missing extensions, roles, unsupported schemas, incomplete grants or any restore SQL error.
docker exec "$name" pg_restore -U postgres -d postgres --no-owner --no-acl   --exit-on-error --single-transaction /tmp/backup.dump >/dev/null
docker exec "$name" psql -U postgres -d postgres -Atqc 'SELECT 1' | grep -qx 1
echo 'PASS: PostgreSQL 17 isolated logical restore completed without pg_restore errors.'
echo 'NOT VERIFIED: Supabase managed services, auth/JWT/RLS behaviour, Storage API object restore.'

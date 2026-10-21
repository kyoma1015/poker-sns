#!/usr/bin/env bash
set -euo pipefail
# Synthetic isolated QA only. Never accept a production connection string.
# Called after test fixtures are populated and before isolated DB cleanup.
[[ "${DOCKER_HOST:-}" == "unix:///var/run/docker.sock" ]] || { echo "Blocked: not local Docker"; exit 2; }
container="pokerid-poll-qa-db"
scratch="poll_restore_qa"
temp_dump="$(mktemp)"
trap 'rm -f "$temp_dump"' EXIT
# Exact isolated fixture tables only. This is NOT a full Supabase platform backup.
tables=(--table=public.post_interactive --table=public.post_interactive_responses --table=public.notifications)
docker exec "$container" pg_dump -U postgres -d postgres -Fc --no-owner --no-acl "${tables[@]}" > "$temp_dump"
test -s "$temp_dump"
# No production data and no remote connection. Reject an unexpected pre-existing DB.
if docker exec "$container" psql -U postgres -d postgres -Atqc "select 1 from pg_database where datname='$scratch'" | grep -q 1; then
  echo "Blocked: restore verification database already exists" >&2
  exit 2
fi
docker exec "$container" createdb -U postgres "$scratch"
# Only pre-data tables and rows; foreign keys to the full application are NOT
# included in this narrow test. Real restoration needs the full Supabase-aware dump.
docker exec -i "$container" pg_restore -U postgres -d "$scratch" \
  --no-owner --no-acl --exit-on-error --section=pre-data --section=data < "$temp_dump"
fingerprint() {
  local db="$1"
  docker exec "$container" psql -U postgres -d "$db" -At -v ON_ERROR_STOP=1 <<'SQL'
select 'post_interactive', count(*), md5(coalesce(string_agg(to_jsonb(t)::text,'|' order by to_jsonb(t)::text),''))
from public.post_interactive t;
select 'post_interactive_responses', count(*), md5(coalesce(string_agg(to_jsonb(t)::text,'|' order by to_jsonb(t)::text),''))
from public.post_interactive_responses t;
select 'notifications', count(*), md5(coalesce(string_agg(to_jsonb(t)::text,'|' order by to_jsonb(t)::text),''))
from public.notifications t;
SQL
}
source_fingerprint="$(fingerprint postgres)"
restored_fingerprint="$(fingerprint "$scratch")"
if [[ "$source_fingerprint" != "$restored_fingerprint" ]]; then
  echo "FAIL: synthetic backup/restore fingerprints differ" >&2
  exit 1
fi
echo "PASS: synthetic pg_dump/pg_restore verified for 3 interactive tables"
echo "$restored_fingerprint"
docker exec "$container" dropdb -U postgres "$scratch"

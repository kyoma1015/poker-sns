#!/usr/bin/env bash
# Synthetic owner/ACL/RLS round-trip test: NO network and NO production credentials.
set -euo pipefail
umask 077
command -v docker >/dev/null || { echo 'Docker is required for synthetic restore'; exit 2; }
tmp="$(mktemp -d)"
chmod 0777 "$tmp" # synthetic, credential-free scratch; container postgres must write dumps
name="video-synthetic-restore-$RANDOM-$$"
cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  rm -rf "$tmp"
}
trap cleanup EXIT
docker run -d --rm --network none --name "$name" -e POSTGRES_PASSWORD=synthetic-ci-only -v "$tmp:/backup" postgres:17 >/dev/null
for i in $(seq 1 60); do
  if docker exec "$name" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$name" pg_isready -U postgres >/dev/null
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U postgres -d postgres <<'SQL'
CREATE ROLE fixture_owner NOLOGIN;
CREATE ROLE fixture_reader NOLOGIN;
CREATE ROLE fixture_blocked NOLOGIN;
CREATE DATABASE fixture_source;
CREATE DATABASE fixture_restored;
SQL
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U postgres -d fixture_source <<'SQL'
CREATE SCHEMA private_data AUTHORIZATION fixture_owner;
GRANT USAGE ON SCHEMA private_data TO fixture_reader, fixture_blocked;
SET ROLE fixture_owner;
CREATE TABLE private_data.entries(id integer PRIMARY KEY, user_name text NOT NULL);
INSERT INTO private_data.entries VALUES (1, 'reader'), (2, 'other');
ALTER TABLE private_data.entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE private_data.entries FORCE ROW LEVEL SECURITY;
CREATE POLICY reader_scope ON private_data.entries FOR SELECT TO fixture_reader USING (user_name = 'reader');
GRANT SELECT ON private_data.entries TO fixture_reader, fixture_blocked;
RESET ROLE;
SQL
docker exec "$name" sh -ec 'pg_dump -U postgres -d fixture_source -Fc -f /backup/synthetic.dump && pg_restore -l /backup/synthetic.dump > /backup/synthetic.toc && test -s /backup/synthetic.toc && pg_restore -U postgres -d fixture_restored --exit-on-error --single-transaction /backup/synthetic.dump'
# Compare source and restored privileges plus verify restrictive behaviour as effective roles.
for db in fixture_source fixture_restored; do
  docker exec -i "$name" psql -v ON_ERROR_STOP=1 -At -U postgres -d "$db" <<'SQL' > "$tmp/$db.results"
SELECT 'owner=' || pg_get_userbyid(relowner)
FROM pg_class WHERE oid = 'private_data.entries'::regclass;
SELECT 'rls=' || relrowsecurity || ',force=' || relforcerowsecurity
FROM pg_class WHERE oid = 'private_data.entries'::regclass;
SELECT 'policy=' || policyname || ':' || roles::text || ':' || qual
FROM pg_policies WHERE schemaname = 'private_data' AND tablename = 'entries';
SELECT 'reader_grant=' || has_table_privilege('fixture_reader','private_data.entries','SELECT');
SELECT 'blocked_grant=' || has_table_privilege('fixture_blocked','private_data.entries','SELECT');
SET ROLE fixture_reader;
SELECT 'reader_rows=' || count(*) FROM private_data.entries;
RESET ROLE;
SET ROLE fixture_blocked;
SELECT 'blocked_rows=' || count(*) FROM private_data.entries;
RESET ROLE;
SQL
done
diff -u "$tmp/fixture_source.results" "$tmp/fixture_restored.results"
grep -Fx 'owner=fixture_owner' "$tmp/fixture_restored.results"
grep -Fx 'rls=true,force=true' "$tmp/fixture_restored.results"
grep -Fx 'reader_grant=true' "$tmp/fixture_restored.results"
grep -Fx 'blocked_grant=true' "$tmp/fixture_restored.results"
grep -Fx 'reader_rows=1' "$tmp/fixture_restored.results"
grep -Fx 'blocked_rows=0' "$tmp/fixture_restored.results"
# Negative control: restore explicitly discarding ownership and ACL must not be certified.
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U postgres -d postgres -c 'CREATE DATABASE fixture_lossy' >/dev/null
docker exec "$name" pg_restore -U postgres -d fixture_lossy --no-owner --no-acl --exit-on-error --single-transaction /backup/synthetic.dump
lossy_owner="$(docker exec "$name" psql -At -U postgres -d fixture_lossy -c "SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid='private_data.entries'::regclass")"
[[ "$lossy_owner" != fixture_owner ]] || { echo 'Negative control unexpectedly preserved owner' >&2; exit 1; }
echo 'PASS: isolated PG17 owner/ACL/RLS restore; effective role tests; lossy restore negative control'
echo 'LIMITATION: synthetic PostgreSQL only, not Supabase platform or production backup restore'

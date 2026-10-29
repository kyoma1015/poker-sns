#!/usr/bin/env bash
# PostgreSQL-backed Storage metadata and bytes restore rehearsal (synthetic, isolated).
set -euo pipefail
umask 077
tmp="$(mktemp -d)"
name="video-storage-metadata-$RANDOM-$$"
cleanup(){ docker rm -f "$name" >/dev/null 2>&1 || true; rm -rf "$tmp"; }
trap cleanup EXIT
mkdir -p "$tmp/bytes/post-videos/user-1"
printf synthetic-video > "$tmp/bytes/post-videos/user-1/clip.mp4"
chmod 0777 "$tmp"
docker run -d --rm --network none --name "$name" -e POSTGRES_PASSWORD=only-synthetic -v "$tmp:/backup" postgres:17 >/dev/null
for i in $(seq 1 45); do
  if docker exec "$name" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$name" pg_isready -U postgres >/dev/null
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U postgres <<'SQL'
CREATE ROLE fixture_storage_reader NOLOGIN;
CREATE DATABASE fixture_source;
CREATE DATABASE fixture_restored;
SQL
docker exec -i "$name" psql -v ON_ERROR_STOP=1 -U postgres -d fixture_source <<'SQL'
CREATE SCHEMA storage;
CREATE TABLE storage.buckets (id text PRIMARY KEY, public boolean NOT NULL, file_size_limit bigint);
CREATE TABLE storage.objects (id uuid PRIMARY KEY, bucket_id text NOT NULL REFERENCES storage.buckets(id), name text NOT NULL, owner_id text NOT NULL, bytes bigint NOT NULL, sha256 text NOT NULL, UNIQUE(bucket_id,name));
INSERT INTO storage.buckets VALUES ('post-videos',false,20971520);
INSERT INTO storage.objects VALUES ('00000000-0000-0000-0000-000000000001','post-videos','user-1/clip.mp4','user-1',15,'a');
ALTER TABLE storage.objects ENABLE ROW LEVEL SECURITY;
CREATE POLICY only_owner ON storage.objects FOR SELECT TO fixture_storage_reader USING (owner_id = current_setting('request.jwt.claim.sub', true));
GRANT USAGE ON SCHEMA storage TO fixture_storage_reader;
GRANT SELECT ON storage.buckets,storage.objects TO fixture_storage_reader;
SQL
# Update metadata with actual byte length and sha256 (no external network / no production).
bytes="$(wc -c < "$tmp/bytes/post-videos/user-1/clip.mp4")"
hash="$(sha256sum "$tmp/bytes/post-videos/user-1/clip.mp4" | cut -d' ' -f1)"
docker exec "$name" psql -v ON_ERROR_STOP=1 -U postgres -d fixture_source -c "UPDATE storage.objects SET bytes=$bytes, sha256='$hash'" >/dev/null
docker exec "$name" sh -ec 'pg_dump -U postgres -Fc -d fixture_source -f /backup/storage-metadata.dump && pg_restore -U postgres -d fixture_restored --exit-on-error --single-transaction /backup/storage-metadata.dump'
for db in fixture_source fixture_restored; do
  docker exec -i "$name" psql -v ON_ERROR_STOP=1 -At -U postgres -d "$db" <<'SQL' > "$tmp/$db.tsv"
SELECT b.id || '|' || b.public || '|' || o.name || '|' || o.owner_id || '|' || o.bytes || '|' || o.sha256 FROM storage.buckets b JOIN storage.objects o ON o.bucket_id=b.id;
SELECT 'rls=' || relrowsecurity FROM pg_class WHERE oid='storage.objects'::regclass;
SET ROLE fixture_storage_reader;
SET request.jwt.claim.sub='user-1';
SELECT 'owner_visible=' || count(*) FROM storage.objects;
SET request.jwt.claim.sub='user-2';
SELECT 'other_visible=' || count(*) FROM storage.objects;
RESET ROLE;
SQL
done
diff -u "$tmp/fixture_source.tsv" "$tmp/fixture_restored.tsv"
grep -Fx 'rls=true' "$tmp/fixture_restored.tsv"
grep -Fx 'owner_visible=1' "$tmp/fixture_restored.tsv"
grep -Fx 'other_visible=0' "$tmp/fixture_restored.tsv"
# Verify that restored DB object's owner, bucket private flag, and byte digests match actual recovered bytes.
python3 - "$tmp/fixture_restored.tsv" "$tmp/bytes" <<'PY'
from pathlib import Path
import hashlib, sys
entries=Path(sys.argv[1]).read_text().splitlines()
records=[line.split('|') for line in entries if line.startswith('post-videos|')]
assert len(records)==1
bucket,public,name,owner,size,expected=records[0]
assert bucket=='post-videos' and public in ('f', 'false') and owner=='user-1'
file=Path(sys.argv[2])/bucket/name
assert file.is_file() and not file.is_symlink()
assert file.stat().st_size==int(size)
assert hashlib.sha256(file.read_bytes()).hexdigest()==expected
print('PASS: restored PostgreSQL Storage metadata, private bucket, effective RLS and actual file byte hash agree')
PY
echo 'LIMITATION: isolated PostgreSQL schema fixture, NOT actual Supabase Storage HTTP service'

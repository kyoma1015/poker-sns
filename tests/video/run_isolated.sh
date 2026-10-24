#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
name="pokerid-video-qa-$$"
if docker inspect "$name" >/dev/null 2>&1; then echo "BLOCKED: container collision"; exit 2; fi
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run -d --name "$name" -e POSTGRES_PASSWORD=video-fixture-only postgres:17 >/dev/null
ready=0
for i in $(seq 1 90); do
  if docker exec "$name" psql -U postgres -d postgres -Atqc 'select 1' 2>/dev/null | grep -qx 1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then echo 'BLOCKED: isolated PostgreSQL not ready'; exit 2; fi
for i in $(seq 1 10); do
  if docker exec "$name" psql -U postgres -d postgres -Atqc 'select 1' 2>/dev/null | grep -qx 1; then break; fi
  sleep 1
done
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/fixture.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < sql/post_short_videos_candidate.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/assertions.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/isolated_insert_once_storage.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
create role service_role nologin;
update public.posts set video_path=null;
alter table public.posts add column if not exists content text not null default '';
alter table public.posts alter column id set default gen_random_uuid();
create unique index if not exists video_qa_posts_video_path_unique
 on public.posts(video_path) where video_path is not null;
SQL
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 -c 'create role anon nologin'
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/isolated_fenced_publish.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/isolated_fenced_rpc_assertions.sql
echo 'PASS: isolated PostgreSQL schema, owner-only RLS, legacy delete and insert-once mutation denial'
echo 'NOT TESTED: Supabase Storage API, signed URLs, media duration, upload cleanup'

# Production-compatible candidate on a separate disposable database in the same container.
docker exec "$name" createdb -U postgres video_production_candidate
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 <<'SQL'
create extension if not exists pgcrypto;
create schema auth;
create schema storage;
create table public.posts(id uuid primary key default gen_random_uuid(),
 user_id uuid not null, content text not null default '',
 post_type text not null default 'normal',image_urls text[] not null default '{}');
create table storage.buckets(id text primary key,name text not null,public boolean not null,
 file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(id uuid primary key default gen_random_uuid(),
 bucket_id text references storage.buckets(id),name text not null,owner_id text);
create function auth.uid() returns uuid language sql stable as $
 select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid $;
grant usage on schema public to video_owner;
SQL
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 <<'SQL'
create unique index storage_objects_bucket_name_unique on storage.objects(bucket_id,name);
insert into public.posts(id,user_id,content) values
 ('11111111-1111-1111-1111-111111111111',
  '10000000-0000-0000-0000-000000000001','preserved existing post');
SQL
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 < tests/video/production_additive_candidate.sql
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 < tests/video/production_candidate_isolated_assertions.sql
echo 'PASS: isolated production-schema-compatible additive migration and fenced RPC assertions'

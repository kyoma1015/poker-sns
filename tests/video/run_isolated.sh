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
create function auth.uid() returns uuid language sql stable as 'select nullif(current_setting(''request.jwt.claim.sub'',true),'''')::uuid';
grant usage on schema public to video_owner;
-- Model production's service_role with BYPASSRLS, but only in this disposable cluster.
alter role service_role bypassrls;
grant usage on schema public,storage to service_role;
grant select,update on storage.objects to service_role;
SQL
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 <<'SQL'
create unique index storage_objects_bucket_name_unique on storage.objects(bucket_id,name);
insert into public.posts(id,user_id,content) values
 ('11111111-1111-1111-1111-111111111111',
  '10000000-0000-0000-0000-000000000001','preserved existing post');
SQL
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 -c 'create role authenticated nologin'
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 < tests/video/production_additive_candidate.sql
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 < tests/video/production_candidate_isolated_assertions.sql
echo 'PASS: isolated production-schema-compatible additive migration and fenced RPC assertions'

# Permanent-key ledger candidate is exercised ONLY in disposable PostgreSQL.
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 <<'SQL'
do $$ begin
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin;
  end if;
end $$;
SQL
# Ledger is already installed by production_additive_candidate.sql; do not reapply it.
docker exec -i "$name" psql -U postgres -d video_production_candidate -v ON_ERROR_STOP=1 <<'SQL'
do $$
declare
  owner uuid := '10000000-0000-0000-0000-000000000001';
  path text := '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4';
  reservation uuid;
begin
  reservation := public.video_reserve_object_key(owner,path);
  if reservation is null then raise exception 'reservation missing'; end if;
  begin
    perform public.video_reserve_object_key(owner,path);
    raise exception 'duplicate reservation accepted';
  exception when unique_violation then null;
  end;
  begin
    perform public.video_reserve_object_key(owner,'10000000-0000-0000-0000-000000000002/30000000-0000-0000-0000-000000000001.mp4');
    raise exception 'foreign owner path accepted';
  exception when raise_exception then
    if SQLERRM <> 'invalid video reservation' then raise; end if;
  end;
  if (select count(*) from public.video_reserved_object_keys) <> 1 then
    raise exception 'reservation ledger mutated';
  end if;
end $$;
-- Verify that app roles cannot mutate the ledger or invoke privileged RPC.
do $$
begin
  if has_function_privilege('authenticated',
       'public.video_reserve_object_key(uuid,text)', 'EXECUTE') then
    raise exception 'authenticated can invoke trusted reservation RPC';
  end if;
  if has_table_privilege('authenticated',
       'public.video_reserved_object_keys', 'DELETE') then
    raise exception 'authenticated can erase key reservations';
  end if;
  if has_table_privilege('anon',
       'public.video_reserved_object_keys', 'INSERT') then
    raise exception 'anon can forge reservations';
  end if;
  if not (select relrowsecurity from pg_class
          where oid='public.video_reserved_object_keys'::regclass) then
    raise exception 'reservation ledger RLS disabled';
  end if;
end $$;
SQL
echo 'PASS: disposable PostgreSQL reservation rejects duplicates and denies client mutation'

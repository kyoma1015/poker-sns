#!/usr/bin/env bash
set -euo pipefail
name="video-rollout-${RANDOM}-$$"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT
docker run -d --rm --network none --name "$name" -e POSTGRES_PASSWORD=synthetic postgres:17 >/dev/null
for i in $(seq 1 60); do docker exec "$name" pg_isready -U postgres >/dev/null 2>&1 && break; sleep 1; done
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
create role anon; create role authenticated; create role service_role bypassrls;
create schema auth; create schema storage; create schema extensions;
create extension pgcrypto schema extensions;
create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid$$;
grant usage on schema auth,storage,public to authenticated,anon;
create table public.posts(id uuid primary key default gen_random_uuid(),user_id uuid,content text,post_type text,image_urls text[]);
alter table public.posts enable row level security;
create policy existing_read on public.posts for select using(true);
create policy existing_insert on public.posts for insert with check(user_id=auth.uid());
create policy existing_update on public.posts for update using(user_id=auth.uid());
create policy existing_delete on public.posts for delete using(user_id=auth.uid());
grant select,insert,update,delete on public.posts to authenticated;
grant select on public.posts to anon;
create table storage.buckets(id text primary key,name text,public boolean,file_size_limit bigint,allowed_mime_types text[]);
create table storage.objects(id uuid default gen_random_uuid(),bucket_id text,name text,owner_id text);
alter table storage.objects enable row level security;
grant select,insert,update,delete on storage.objects to authenticated;
-- Existing permissive policies for unrelated buckets must remain usable.
create policy existing_other_insert on storage.objects for insert to authenticated with check(bucket_id='post-images');
create policy existing_other_update on storage.objects for update to authenticated using(bucket_id='post-images') with check(bucket_id='post-images');
create policy existing_other_delete on storage.objects for delete to authenticated using(bucket_id='post-images');
SQL
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < sql/video_production_limited_rollout.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
insert into auth.users values('11111111-1111-4111-8111-111111111111');
insert into video_private.allowed_publishers values('11111111-1111-4111-8111-111111111111',true);
set role authenticated;
set request.jwt.claim.sub='11111111-1111-4111-8111-111111111111';
do $$begin if public.video_rollout_allowed() then raise exception 'default must be off'; end if; end$$;
insert into public.posts(user_id,content,post_type,image_urls) values(auth.uid(),'retained normal post','normal','{}');
do $$begin
 begin insert into public.posts(user_id,video_path) values(auth.uid(),'forged'); raise exception 'direct video insert succeeded';
 exception when insufficient_privilege then null; end;
end$$;
reset role;
update video_private.rollout_settings set enabled=true;
set role authenticated;
do $$begin if not public.video_rollout_allowed() then raise exception 'allowed owner denied'; end if; end$$;
select public.video_reserve_object_key(auth.uid(),'11111111-1111-4111-8111-111111111111/22222222-2222-4222-8222-222222222222.mp4');
set request.jwt.claim.sub='33333333-3333-4333-8333-333333333333';
do $$begin if public.video_rollout_allowed() then raise exception 'other owner allowed'; end if; end$$;
reset role;
update video_private.rollout_settings set enabled=false;
set role authenticated;
set request.jwt.claim.sub='11111111-1111-4111-8111-111111111111';
do $$begin if public.video_rollout_allowed() then raise exception 'stop failed'; end if; end$$;
select count(*)=1 as normal_post_retained from public.posts;
SQL
echo 'PASS: additive migration; default off; DB allowlist; direct INSERT rejected; reservation; other owner denied; emergency stop; normal post retained'
echo 'LIMITATION: synthetic JWT claims in PG17, not real Auth/HTTP/Chromium publication E2E'

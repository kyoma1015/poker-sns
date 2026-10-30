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
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 <<'SQL'
do $test$
declare
 owner uuid := '11111111-1111-4111-8111-111111111111';
 path text := '11111111-1111-4111-8111-111111111111/44444444-4444-4444-8444-444444444444.mp4';
 generation uuid := gen_random_uuid(); secret bytea := extensions.gen_random_bytes(32);
 nonce bytea := extensions.gen_random_bytes(16); hash text := repeat('a',64);
 expiry bigint := extract(epoch from clock_timestamp())::bigint+120;
 payload bytea; signature text; post uuid; key_id smallint := 1;
begin
 update video_private.rollout_settings set enabled=true;
 insert into video_private.attestation_keys values(key_id,secret,true);
 insert into public.video_reserved_object_keys(bucket_id,object_path,owner_id) values('post-videos',path,owner);
 insert into storage.objects(id,bucket_id,name,owner_id) values(generation,'post-videos',path,owner::text);
 payload := decode('01','hex')||decode(replace(owner::text,'-',''),'hex')||
 set_byte(decode('00','hex'),0,octet_length(convert_to(path,'UTF8')))||convert_to(path,'UTF8')||
 decode(replace(generation::text,'-',''),'hex')||decode(hash,'hex')||pg_catalog.int4send(1000)||
 extensions.digest(convert_to('signed fixture','UTF8'),'sha256')||pg_catalog.int8send(expiry)||nonce;
 signature := encode(extensions.hmac(payload,secret,'sha256'),'hex');
 perform set_config('request.jwt.claim.sub',owner::text,true);
 execute 'set local role authenticated';
 post := public.video_publish_attested_v1(owner,path,generation,hash,1000,'signed fixture',expiry,encode(nonce,'hex'),signature,key_id);
 begin
  perform public.video_publish_attested_v1(owner,path,generation,hash,1000,'signed fixture',expiry,encode(nonce,'hex'),signature,key_id);
  raise exception 'nonce reused';
 exception when unique_violation then null; end;
 perform set_config('request.jwt.claim.sub','33333333-3333-4333-8333-333333333333',true);
 begin perform public.video_hide_own(post); raise exception 'other owner hid post';
 exception when raise_exception then if sqlerrm<>'video user denied' then raise; end if; end;
 perform set_config('request.jwt.claim.sub',owner::text,true);
 execute 'reset role';
 update video_private.rollout_settings set enabled=false;
 execute 'set local role authenticated';
 if public.video_rollout_allowed() then raise exception 'emergency stop failed'; end if;
 if not public.video_hide_own(post) or not public.video_hide_own(post) then raise exception 'hide failed'; end if;
 update storage.objects set name=name where name=path;
 if found then raise exception 'Storage update allowed'; end if;
 delete from storage.objects where name=path;
 if found then raise exception 'Storage delete allowed'; end if;
 if exists(select 1 from public.posts where id=post) then raise exception 'hidden post visible'; end if;
 if exists(select 1 from storage.objects where name=path) then raise exception 'hidden bytes visible'; end if;
 execute 'reset role';
 if (select count(*) from public.posts where video_path=path)<>1 then raise exception 'post not retained exactly once'; end if;
 if (select count(*) from storage.objects where name=path)<>1 then raise exception 'Storage object deleted'; end if;
end $test$;
SQL
echo 'PASS: additive migration; default off; DB allowlist; direct INSERT rejected; reservation; other owner denied; emergency stop; normal post retained'
echo 'LIMITATION: synthetic JWT claims in PG17, not real Auth/HTTP/Chromium publication E2E'

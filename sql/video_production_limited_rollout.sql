-- FIRST-INSTALL CANDIDATE. Requires explicit owner approval. No production execution.
begin;
-- STAGED CANDIDATE ONLY. Do not execute until full production-equivalent tests pass.
-- Additive changes: never drop or modify existing posts data/policies.

alter table public.posts add column if not exists video_path text;
alter table public.posts add column if not exists video_generation uuid;
alter table public.posts add column if not exists video_sha256 text;
alter table public.posts add column if not exists video_duration_seconds double precision;
create unique index if not exists poker_posts_video_path_unique on public.posts(video_path) where video_path is not null;
-- Do not grant broad posts privileges to service_role for video publication.
-- Privileged mutations are not an acceptable authorization boundary.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values ('post-videos','post-videos',false,20971520,array['video/mp4','video/webm']::text[])
on conflict (id) do nothing;
-- Explicitly forbid a conflicting pre-existing bucket configuration.
do $$
begin
 if not exists(select 1 from storage.buckets where id='post-videos' and public=false
   and file_size_limit=20971520
   and allowed_mime_types @> array['video/mp4','video/webm']::text[]) then
   raise exception 'post-videos bucket configuration mismatch';
 end if;
 -- Do not touch existing unrelated Storage policies. No post-videos UPDATE/DELETE.
 if exists(select 1 from pg_policies where schemaname='storage' and tablename='objects'
  and cmd in ('UPDATE','DELETE','ALL') and
  (coalesce(qual,'') ilike '%post-videos%' or coalesce(with_check,'') ilike '%post-videos%'))
 then raise exception 'mutable video Storage policy exists'; end if;
end $$;

-- Permanent reservations must precede every authenticated video upload.
create table if not exists public.video_reserved_object_keys (
  bucket_id text not null check (bucket_id = 'post-videos'),
  object_path text not null,
  owner_id uuid not null,
  reservation_id uuid not null default gen_random_uuid(),
  created_at timestamptz not null default now(),
  primary key (bucket_id, object_path),
  unique (reservation_id),
  check (object_path ~ (
    '^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/' ||
    '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](mp4|webm)$'
  ))
);
alter table public.video_reserved_object_keys enable row level security;
revoke all on public.video_reserved_object_keys from public, anon, authenticated;
-- No INSERT/UPDATE/DELETE policies: reservation is append-only through
-- a narrowly scoped trusted server RPC. Never grant table DELETE.

create function public.video_reserve_object_key(
  p_owner uuid, p_path text
) returns uuid language plpgsql security definer
set search_path = '' as $$
declare
  v_id uuid;
begin
  if not public.video_rollout_allowed() then raise exception 'video rollout disabled'; end if;
  -- Caller identity is the sole reservation authority; do not trust p_owner.
  if (select auth.uid()) is distinct from p_owner then
    raise exception 'reservation owner mismatch';
  end if;
  if p_owner is null or p_path is null
     or p_path !~ ('^' || p_owner::text ||
       '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](mp4|webm)$')
  then
    raise exception 'invalid video reservation';
  end if;
  -- Serialize reservations per owner to prevent concurrent calls bypassing
  -- rolling-window quotas. This ledger is append-only, so abandoned uploads
  -- consume quota instead of allowing unbounded permanent key reservations.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_owner::text, 72941));
  if (select count(*) from public.video_reserved_object_keys
      where owner_id=p_owner and created_at>pg_catalog.clock_timestamp()-interval '1 hour') >= 12
     or (select count(*) from public.video_reserved_object_keys
      where owner_id=p_owner and created_at>pg_catalog.clock_timestamp()-interval '24 hours') >= 80
  then
    raise exception 'video reservation rate limit exceeded';
  end if;
  -- Do not use ON CONFLICT DO UPDATE or return an existing reservation.
  -- A collision must fail permanently, including a deleted Storage object.
  insert into public.video_reserved_object_keys(bucket_id,object_path,owner_id)
    values ('post-videos',p_path,p_owner)
    returning reservation_id into v_id;
  return v_id;
end;
$$;
revoke all on function public.video_reserve_object_key(uuid,text)
  from public, anon;
grant execute on function public.video_reserve_object_key(uuid,text) to authenticated;
-- Read-only owner predicate for a future Storage INSERT policy.
-- SECURITY DEFINER bypasses ledger RLS without exposing the ledger itself.
-- Only the exact authenticated owner and reserved path may match.
create function public.video_reserved_key_is_owned(
  p_path text, p_owner uuid
) returns boolean language sql stable security definer
set search_path = '' as $reserved_owner$
  select p_owner is not null
    and p_owner = (select auth.uid())
    and exists (
      select 1 from public.video_reserved_object_keys r
      where r.bucket_id = 'post-videos'
        and r.object_path = p_path
        and r.owner_id = p_owner
    );
$reserved_owner$;
revoke all on function public.video_reserved_key_is_owned(text,uuid)
  from public, anon;
grant execute on function public.video_reserved_key_is_owned(text,uuid)
  to authenticated;
-- This helper is a prerequisite only; it does not fence permissive INSERT
-- policies, privileged service_role Storage writes, or upserts.


-- Only the authenticated owner can reserve. No service_role grant.
-- Refuse pre-existing video writer policies instead of silently OR-combining them.
do $video_policy_guard$ begin
 if exists(select 1 from pg_policies where schemaname='storage' and tablename='objects'
 and (coalesce(qual,'') ilike '%post-videos%' or coalesce(with_check,'') ilike '%post-videos%'))
 then raise exception 'existing video writer policy requires audit'; end if;
end $video_policy_guard$;
create policy poker_post_videos_insert_once on storage.objects for insert to authenticated
with check(bucket_id='post-videos' and
 split_part(name,'/',1)=(select auth.uid())::text and
 name ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$' and
 public.video_reserved_key_is_owned(name,(select auth.uid())));
create policy poker_post_videos_read_own on storage.objects for select to authenticated
using(bucket_id='post-videos' and split_part(name,'/',1)=(select auth.uid())::text);
-- Viewer access is limited to objects referenced by a post visible under
-- the caller's existing public.posts SELECT RLS. Unpublished staging keys
-- remain owner-only. This is an invoker-RLS subquery, NOT SECURITY DEFINER.
-- No is_public column is assumed: production posts visibility is the authority.
create policy poker_post_videos_read_visible_post on storage.objects
for select to authenticated
using (
  bucket_id='post-videos'
  and exists (
    select 1 from public.posts p
    where p.video_path=storage.objects.name
      and p.user_id::text=split_part(storage.objects.name,'/',1)
  )
);
-- SELECT policies do not grant UPDATE/DELETE; the complete set of existing
-- permissive policies and privileged writers still requires release audit.
-- A permissive policy for ALL or UPDATE/DELETE can override bucket-specific
-- policy assumptions. Reject broad policies unless explicitly bucket-scoped away.
-- Production inspection on 2026-10-25 found only bucket-scoped mutations.
do $guard$
begin
 if exists(
  select 1 from pg_policies where schemaname='storage' and tablename='objects'
   and cmd in ('ALL','UPDATE','DELETE')
   and (coalesce(qual,'') not like '%bucket_id%'
     or (cmd in ('ALL','UPDATE') and coalesce(with_check,'') not like '%bucket_id%'))
 ) then raise exception 'unscoped Storage mutation policy blocks video release'; end if;
end $guard$;
-- Release blocker: permissive INSERT/ALL policies combine by OR, including
-- policies whose names never mention post-videos. Reject any unscoped writer.
-- A textual bucket predicate is only a screening check; review every policy
-- expression and every privileged writer before production application.
do $video_insert_or_guard$
begin
 if exists (
   select 1 from pg_policies
   where schemaname='storage' and tablename='objects'
     and permissive='PERMISSIVE' and cmd in ('INSERT','ALL')
     and (coalesce(with_check,'') not ilike '%bucket_id%')
 ) then
   raise exception 'unscoped permissive Storage INSERT/ALL policy blocks video release';
 end if;
end $video_insert_or_guard$;
-- No authenticated UPDATE/DELETE policy for post-videos. No public read policy.
create function public.video_production_storage_generation(p_owner uuid,p_path text)
returns uuid language plpgsql security definer set search_path='' as $$
declare v uuid;
begin
 if (select auth.uid()) is distinct from p_owner or
    split_part(p_path,'/',1)<>p_owner::text then raise exception 'trusted owner required'; end if;
 select id into v from storage.objects where bucket_id='post-videos' and name=p_path
   and owner_id=p_owner::text;
 return v;
end $$;
revoke all on function public.video_production_storage_generation(uuid,text) from public,anon,service_role;
grant execute on function public.video_production_storage_generation(uuid,text) to authenticated;
create function public.video_production_publish_fenced(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration double precision,p_content text)
returns uuid language plpgsql security definer set search_path='' as $$
declare v uuid;
begin
 if (select auth.uid()) is distinct from p_owner then raise exception 'video owner mismatch'; end if;
 if p_path !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$'
 or split_part(p_path,'/',1)<>p_owner::text or p_sha256 !~ '^[0-9a-f]{64}$'
 or p_duration<=0 or p_duration>30 or p_duration='NaN'::float8
 or length(p_content)>10000 then raise exception 'invalid fenced publication'; end if;
 perform 1 from storage.objects where bucket_id='post-videos' and name=p_path
 and id=p_generation and owner_id=p_owner::text for update;
 if not found then raise exception 'Storage generation mismatch'; end if;
 insert into public.posts(user_id,content,post_type,image_urls,video_path,
  video_generation,video_sha256,video_duration_seconds)
 values(p_owner,p_content,'normal','{}'::text[],p_path,p_generation,p_sha256,p_duration)
 on conflict(video_path) where video_path is not null do nothing returning id into v;
 if v is null then
 select id into v from public.posts where user_id=p_owner and video_path=p_path
 and video_generation=p_generation and video_sha256=p_sha256
 and video_duration_seconds=p_duration and content=p_content;
 end if;
 if v is null then raise exception 'conflicting prior video publication'; end if;
 return v;
end $$;
revoke all on function public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text) from public,anon,service_role;
-- FAIL CLOSED: owner JWT cannot supply trusted ffprobe metadata. A future
-- server-attested publication path must be independently verified before grant.
-- No authenticated or service_role EXECUTE until that implementation exists.
create function public.video_production_reconcile_fenced(p_owner uuid,p_path text,p_generation uuid)
returns uuid language plpgsql security definer set search_path='' as $$
declare v uuid;
begin
 if (select auth.uid()) is distinct from p_owner then raise exception 'video owner mismatch'; end if;
 select id into v from public.posts where user_id=p_owner and video_path=p_path
 and video_generation=p_generation;
 return v;
end $$;
revoke all on function public.video_production_reconcile_fenced(uuid,text,uuid) from public,anon,service_role;
grant execute on function public.video_production_reconcile_fenced(uuid,text,uuid) to authenticated;
-- REVIEW ONLY: append to production_additive_candidate.sql only after disposable QA.
-- Provision key via separate DBA-controlled transaction, never in source or migration.
-- This table is not in an exposed PostgREST schema.
create schema if not exists video_private;
revoke all on schema video_private from public,anon,authenticated,service_role;
create table if not exists video_private.attestation_keys(
 key_id smallint primary key, secret bytea not null check(octet_length(secret)=32), active boolean not null default false
);
revoke all on video_private.attestation_keys from public,anon,authenticated,service_role;
create table if not exists video_private.consumed_nonces(
 nonce bytea primary key check(octet_length(nonce)=16), owner_id uuid not null,
 object_path text not null, created_at timestamptz not null default now()
);
revoke all on video_private.consumed_nonces from public,anon,authenticated,service_role;
-- The signing secret must be installed separately and atomically on both server and DB.
-- PostgreSQL pgcrypto is required; no secret or provisioning endpoint is exposed.
create extension if not exists pgcrypto;
-- Included inside the additive production migration transaction. Default OFF.
create table video_private.rollout_settings(
 singleton boolean primary key default true check(singleton), enabled boolean not null default false
);
insert into video_private.rollout_settings(singleton,enabled) values(true,false);
create table video_private.allowed_publishers(
 user_id uuid primary key references auth.users(id), enabled boolean not null default false
);
create table video_private.hidden_videos(
 post_id uuid primary key references public.posts(id), hidden_at timestamptz not null default clock_timestamp()
);
revoke all on all tables in schema video_private from public,anon,authenticated,service_role;
create function public.video_rollout_member() returns boolean
language sql stable security definer set search_path='' as $$
 select auth.uid() is not null and exists(select 1 from video_private.allowed_publishers
 where user_id=auth.uid() and enabled)
$$;
create function public.video_rollout_allowed() returns boolean
language sql volatile security definer set search_path='' as $$
 select public.video_rollout_member() and exists(select 1 from video_private.rollout_settings where singleton and enabled)
$$;
create function public.video_rollout_visible(p_path text) returns boolean
language sql stable security definer set search_path='' as $$
 select not exists(select 1 from video_private.hidden_videos h join public.posts p on p.id=h.post_id where p.video_path=p_path)
$$;
-- posts SELECT policy must not call a helper that reads posts: that would recurse.
create function public.video_rollout_post_visible(p_id uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select not exists(select 1 from video_private.hidden_videos where post_id=p_id)
$$;
create function public.video_hide_own(p_post_id uuid) returns boolean
language plpgsql security definer set search_path='' as $$
begin
 if not public.video_rollout_member() then raise exception 'video user denied'; end if;
 perform 1 from public.posts where id=p_post_id and user_id=auth.uid() and video_path is not null for update;
 if not found then raise exception 'video owner denied'; end if;
 insert into video_private.hidden_videos(post_id) values(p_post_id) on conflict do nothing;
 return true;
end $$;
revoke all on function public.video_rollout_member(),public.video_rollout_allowed(),public.video_rollout_visible(text),public.video_rollout_post_visible(uuid),public.video_hide_own(uuid) from public,anon,service_role;
grant execute on function public.video_rollout_member(),public.video_rollout_allowed(),public.video_rollout_visible(text),public.video_rollout_post_visible(uuid),public.video_hide_own(uuid) to authenticated;
-- Restrictive AND policies cannot widen existing permissive policies. Normal
-- posts and all other buckets retain their existing RLS/grants unchanged.
create policy video_rollout_posts_read on public.posts as restrictive for select to authenticated
 using(video_path is null or (public.video_rollout_member() and public.video_rollout_post_visible(id)));
create policy video_rollout_posts_insert on public.posts as restrictive for insert to authenticated with check(video_path is null);
create policy video_rollout_posts_update on public.posts as restrictive for update to authenticated
 using(video_path is null) with check(video_path is null);
create policy video_rollout_posts_delete on public.posts as restrictive for delete to authenticated using(video_path is null);
create policy video_rollout_storage_insert on storage.objects as restrictive for insert to authenticated
 with check(bucket_id<>'post-videos' or (public.video_rollout_allowed() and owner_id=auth.uid()::text and public.video_reserved_key_is_owned(name,auth.uid())));
create policy video_rollout_storage_read on storage.objects as restrictive for select to authenticated
 using(bucket_id<>'post-videos' or (public.video_rollout_member() and public.video_rollout_visible(name)));
create policy video_rollout_storage_update on storage.objects as restrictive for update to authenticated
 using(bucket_id<>'post-videos') with check(bucket_id<>'post-videos');
create policy video_rollout_storage_delete on storage.objects as restrictive for delete to authenticated using(bucket_id<>'post-videos');
-- Emergency stop: administrator sets rollout_settings.enabled=false. No row or
-- object deletion. Administrators can hide abusive video by inserting its post_id
-- into hidden_videos; no client DELETE or Storage mutation permission is added.
create function public.video_publish_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $fn$
declare
 v_secret bytea;v_payload bytea;v_expected bytea;v_signature bytea;
 v_path bytea;v_id uuid;v_existing public.posts%rowtype;
begin
 if not public.video_rollout_allowed() then raise exception 'video rollout disabled'; end if;
 if (select auth.uid()) is distinct from p_owner then raise exception 'video owner mismatch'; end if;
 -- SQL three-valued logic must never turn a NULL proof into authorization.
 if p_owner is null or p_generation is null or p_path is null or
  p_sha256 is null or p_nonce is null or p_signature is null or
  p_duration_ms is null or p_expires_at is null or p_key_id is null or
  p_path !~ ('^'||p_owner::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$') or
  p_sha256 !~ '^[0-9a-f]{64}$' or p_nonce !~ '^[0-9a-f]{32}$' or
  p_signature !~ '^[0-9a-f]{64}$' or p_duration_ms not between 1 and 30000 or
  p_content is null or length(p_content)>10000 or
  p_expires_at <= extract(epoch from clock_timestamp())::bigint or
  p_expires_at > extract(epoch from clock_timestamp())::bigint+300 or
  p_expires_at<0 then raise exception 'invalid attestation claims'; end if;
 v_path:=convert_to(p_path,'UTF8');
 if octet_length(v_path)>255 then raise exception 'path too long'; end if;
 select secret into v_secret from video_private.attestation_keys where key_id=p_key_id and active=true;
 if v_secret is null then raise exception 'attestation key unavailable'; end if;
 v_payload:=decode('01','hex')||decode(replace(p_owner::text,'-',''),'hex')||
  set_byte(decode('00','hex'),0,octet_length(v_path))||v_path||
  decode(replace(p_generation::text,'-',''),'hex')||decode(p_sha256,'hex')||
  pg_catalog.int4send(p_duration_ms)||
  extensions.digest(convert_to(p_content,'UTF8'),'sha256')||
  pg_catalog.int8send(p_expires_at)||decode(p_nonce,'hex');
 v_expected:=extensions.hmac(v_payload,v_secret,'sha256');
 v_signature:=decode(p_signature,'hex');
 -- Compare all bytes, with no early exit on mismatched prefix.
 if v_expected is null or v_signature is null or
   octet_length(v_expected)<>octet_length(v_signature) or
   (select bit_or(get_byte(v_expected,n) # get_byte(v_signature,n))
    from generate_series(0,31) as n)<>0 then
  raise exception 'invalid video attestation'; end if;
 perform 1 from public.video_reserved_object_keys
  where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found then raise exception 'missing owner reservation'; end if;
 perform 1 from storage.objects where bucket_id='post-videos' and name=p_path
  and id=p_generation and owner_id=p_owner::text for update;
 if not found then raise exception 'Storage generation mismatch'; end if;
 if p_expires_at <= extract(epoch from clock_timestamp())::bigint or not public.video_rollout_allowed() then raise exception 'expired or stopped video publication'; end if;
 if not exists(select 1 from public.video_reserved_object_keys where object_path=p_path and owner_id=p_owner and created_at>clock_timestamp()-interval '1 hour') then raise exception 'expired video reservation'; end if;
 -- Single-use nonce is consumed in the SAME transaction as post publication.
 insert into video_private.consumed_nonces(nonce,owner_id,object_path)
 values(decode(p_nonce,'hex'),p_owner,p_path);
 insert into public.posts(user_id,content,post_type,image_urls,video_path,
  video_generation,video_sha256,video_duration_seconds)
 values(p_owner,p_content,'normal','{}'::text[],p_path,p_generation,p_sha256,p_duration_ms::double precision/1000)
 on conflict(video_path) where video_path is not null do nothing returning id into v_id;
 if v_id is null then
  select * into v_existing from public.posts where video_path=p_path;
  if v_existing.user_id<>p_owner or v_existing.video_generation<>p_generation or
   v_existing.video_sha256<>p_sha256 or
   v_existing.video_duration_seconds<>p_duration_ms::double precision/1000 or
   v_existing.content<>p_content then raise exception 'conflicting prior video publication'; end if;
  v_id:=v_existing.id;
 end if;
 if v_id is null then raise exception 'publication failed'; end if;
 return v_id;
end $fn$;
revoke all on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,authenticated,service_role;
-- Grant to authenticated only after production-equivalent isolated tests and secret provisioning.
-- grant execute on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;


grant execute on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;
create policy video_rollout_anon_posts on public.posts as restrictive for select to anon using(video_path is null);
create policy video_rollout_anon_storage on storage.objects as restrictive for select to anon using(bucket_id<>'post-videos');
commit;

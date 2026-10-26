-- STAGED CANDIDATE ONLY. Do not execute until full production-equivalent tests pass.
-- Additive changes: never drop or modify existing posts data/policies.
begin;
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

create or replace function public.video_reserve_object_key(
  p_owner uuid, p_path text
) returns uuid language plpgsql security definer
set search_path = '' as $$
declare
  v_id uuid;
begin
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
create or replace function public.video_reserved_key_is_owned(
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
-- No authenticated UPDATE/DELETE policy for post-videos. No public read policy.
create or replace function public.video_production_storage_generation(p_owner uuid,p_path text)
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
create or replace function public.video_production_publish_fenced(
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
create or replace function public.video_production_reconcile_fenced(p_owner uuid,p_path text,p_generation uuid)
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
commit;

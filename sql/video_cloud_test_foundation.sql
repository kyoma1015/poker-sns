-- Dedicated empty cloud test database only. No production application tables.
begin;
do $$ begin
 if current_setting('video.cloud_test_project_ref',true) is distinct from 'hbhyuotzginwysrineyo' then
  raise exception 'dedicated cloud test target attestation required';
 end if;
 if exists(select 1 from storage.buckets) or exists(select 1 from storage.objects) then
  raise exception 'requires empty dedicated Storage';
 end if;
 if exists(select 1 from public.posts limit 1) then
  raise exception 'requires empty dedicated test database';
 end if;
exception when undefined_table then null; end $$;
create schema video_cloud;
revoke all on schema video_cloud from public,anon,authenticated,service_role;
create table video_cloud.allowed_users(
 user_id uuid primary key references auth.users(id), enabled boolean not null default false
);
create table video_cloud.reservations(
 path text primary key, owner_id uuid not null references auth.users(id),
 sha256 text not null check(sha256 ~ '^[0-9a-f]{64}$'),
 size bigint not null check(size between 1 and 20971520),
 mime text not null check(mime in ('video/mp4','video/webm')),
 content text not null check(length(content)<=10000),
 created_at timestamptz not null default clock_timestamp(),
 expires_at timestamptz not null default clock_timestamp()+interval '1 hour',
 check(path ~ ('^'||owner_id::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$')),
 check((mime='video/mp4' and path like '%.mp4') or (mime='video/webm' and path like '%.webm'))
);
alter table video_cloud.allowed_users enable row level security;
alter table video_cloud.reservations enable row level security;
revoke all on all tables in schema video_cloud from public,anon,authenticated,service_role;
create function public.video_cloud_allowed() returns boolean
language sql stable security definer set search_path='' as $$
 select auth.uid() is not null and exists(
 select 1 from video_cloud.allowed_users where user_id=auth.uid() and enabled)
$$;
revoke all on function public.video_cloud_allowed() from public,anon,service_role;
grant execute on function public.video_cloud_allowed() to authenticated;
create function public.video_cloud_reserve(p_path text,p_sha256 text,p_size bigint,p_mime text,p_content text)
returns timestamptz language plpgsql security definer set search_path='' as $$
declare r video_cloud.reservations%rowtype;
begin
 if not public.video_cloud_allowed() or auth.uid() is null then raise exception 'test user denied'; end if;
 if p_path is null or split_part(p_path,'/',1)<>auth.uid()::text then raise exception 'owner denied'; end if;
 -- Serialize same-owner reservations and quota decisions across tabs.
 perform pg_advisory_xact_lock(hashtextextended(auth.uid()::text,0));
 select * into r from video_cloud.reservations where path=p_path for update;
 if found then
  if r.owner_id<>auth.uid() or r.sha256 is distinct from p_sha256 or r.size is distinct from p_size
   or r.mime is distinct from p_mime or r.content is distinct from p_content
   or r.expires_at<=clock_timestamp() then raise exception 'reservation conflict'; end if;
  return r.expires_at;
 end if;
 if (select count(*) from video_cloud.reservations where owner_id=auth.uid())>=10 then
  raise exception 'test quota exceeded'; end if;
 insert into video_cloud.reservations(path,owner_id,sha256,size,mime,content)
 values(p_path,auth.uid(),p_sha256,p_size,p_mime,p_content) returning * into r;
 return r.expires_at;
end $$;
revoke all on function public.video_cloud_reserve(text,text,bigint,text,text) from public,anon,service_role;
grant execute on function public.video_cloud_reserve(text,text,bigint,text,text) to authenticated;
create function public.video_cloud_upload_allowed(p_name text) returns boolean
language sql stable security definer set search_path='' as $$
 select public.video_cloud_allowed() and exists(
 select 1 from video_cloud.reservations where path=p_name and owner_id=auth.uid() and expires_at>clock_timestamp())
$$;
revoke all on function public.video_cloud_upload_allowed(text) from public,anon,service_role;
grant execute on function public.video_cloud_upload_allowed(text) to authenticated;
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('post-videos','post-videos',false,20971520,array['video/mp4','video/webm']);
create policy video_cloud_insert on storage.objects for insert to authenticated
with check(bucket_id='post-videos' and owner_id=auth.uid()::text and public.video_cloud_upload_allowed(name));
create policy video_cloud_read on storage.objects for select to authenticated
using(bucket_id='post-videos' and owner_id=auth.uid()::text and public.video_cloud_allowed());
-- No UPDATE/DELETE policies: fresh dedicated project is a prerequisite.
commit;

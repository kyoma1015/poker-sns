-- STAGED CANDIDATE ONLY. Do not execute until full production-equivalent tests pass.
-- Additive changes: never drop or modify existing posts data/policies.
begin;
alter table public.posts add column if not exists video_path text;
alter table public.posts add column if not exists video_generation uuid;
alter table public.posts add column if not exists video_sha256 text;
alter table public.posts add column if not exists video_duration_seconds double precision;
create unique index if not exists poker_posts_video_path_unique on public.posts(video_path) where video_path is not null;
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
create policy poker_post_videos_insert_once on storage.objects for insert to authenticated
with check(bucket_id='post-videos' and
 split_part(name,'/',1)=(select auth.uid())::text and
 name ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$');
create policy poker_post_videos_read_own on storage.objects for select to authenticated
using(bucket_id='post-videos' and split_part(name,'/',1)=(select auth.uid())::text);
-- No authenticated UPDATE/DELETE policy for post-videos. No public read policy.
create or replace function public.video_production_storage_generation(p_owner uuid,p_path text)
returns uuid language plpgsql security invoker set search_path='' as $$
declare v uuid;
begin
 if current_user not in ('postgres','service_role') or
    split_part(p_path,'/',1)<>p_owner::text then raise exception 'trusted owner required'; end if;
 select id into v from storage.objects where bucket_id='post-videos' and name=p_path
   and owner_id=p_owner::text;
 return v;
end $$;
revoke all on function public.video_production_storage_generation(uuid,text) from public,anon,authenticated;
grant execute on function public.video_production_storage_generation(uuid,text) to service_role;
create or replace function public.video_production_publish_fenced(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration double precision,p_content text)
returns uuid language plpgsql security invoker set search_path='' as $$
declare v uuid;
begin
 if current_user not in ('postgres','service_role') then raise exception 'trusted role required'; end if;
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
revoke all on function public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text) from public,anon,authenticated;
grant execute on function public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text) to service_role;
create or replace function public.video_production_reconcile_fenced(p_owner uuid,p_path text,p_generation uuid)
returns uuid language plpgsql security invoker set search_path='' as $$
declare v uuid;
begin
 if current_user not in ('postgres','service_role') then raise exception 'trusted role required'; end if;
 select id into v from public.posts where user_id=p_owner and video_path=p_path
 and video_generation=p_generation;
 return v;
end $$;
revoke all on function public.video_production_reconcile_fenced(uuid,text,uuid) from public,anon,authenticated;
grant execute on function public.video_production_reconcile_fenced(uuid,text,uuid) to service_role;
commit;

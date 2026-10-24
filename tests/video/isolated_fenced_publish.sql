-- DISPOSABLE ISOLATED SUPABASE ONLY. NEVER APPLY TO PRODUCTION.
-- Requires isolated_finalize_db.sql and immutable post-videos Storage policies.
-- The Storage object id is a generation fence ONLY if client UPDATE and DELETE
-- are globally forbidden and the bucket uses unique(bucket_id,name).
alter table public.posts add column if not exists video_generation uuid;
alter table public.posts add column if not exists video_sha256 text;
alter table public.posts add column if not exists video_duration_seconds double precision;

create or replace function public.video_qa_publish_fenced(
 p_owner uuid, p_path text, p_generation uuid, p_sha256 text,
 p_duration double precision, p_content text
) returns uuid language plpgsql security invoker
set search_path = '' as $$
declare v_id uuid;
begin
 if current_user not in ('postgres','service_role') then
  raise exception 'trusted role required';
 end if;
 if p_path !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$'
    or split_part(p_path,'/',1) <> p_owner::text
    or p_sha256 !~ '^[0-9a-f]{64}$'
    or p_duration <= 0 or p_duration > 30
    or p_duration = 'NaN'::float8
    or length(p_content) > 10000 then
  raise exception 'invalid fenced publication';
 end if;
 -- Row lock is meaningful only with an independently audited insert-once
 -- Storage policy: no client or alternate privileged object replacement.
 perform 1 from storage.objects s
  where s.bucket_id='post-videos' and s.name=p_path
    and s.id=p_generation and s.owner_id=p_owner::text
  for update;
 if not found then raise exception 'Storage generation mismatch'; end if;
 insert into public.posts(user_id,content,image_urls,video_path,
                          video_generation,video_sha256,video_duration_seconds)
 values (p_owner,p_content,'{}'::text[],p_path,p_generation,p_sha256,p_duration)
 on conflict (video_path) where video_path is not null do nothing
 returning id into v_id;
 if v_id is null then
  select id into v_id from public.posts
   where user_id=p_owner and video_path=p_path and video_generation=p_generation
     and video_sha256=p_sha256 and video_duration_seconds=p_duration
     and content=p_content;
 end if;
 if v_id is null then raise exception 'conflicting prior video publication'; end if;
 return v_id;
end $$;
revoke all on function public.video_qa_publish_fenced(uuid,text,uuid,text,double precision,text)
 from public,anon,authenticated;
grant execute on function public.video_qa_publish_fenced(uuid,text,uuid,text,double precision,text)
 to service_role;

create or replace function public.video_qa_reconcile_fenced(
 p_owner uuid,p_path text,p_generation uuid
) returns uuid language plpgsql security invoker set search_path='' as $$
declare v_id uuid;
begin
 if current_user not in ('postgres','service_role') then
  raise exception 'trusted role required';
 end if;
 select id into v_id from public.posts
 where user_id=p_owner and video_path=p_path and video_generation=p_generation;
 return v_id;
end $$;
revoke all on function public.video_qa_reconcile_fenced(uuid,text,uuid)
 from public,anon,authenticated;
grant execute on function public.video_qa_reconcile_fenced(uuid,text,uuid)
 to service_role;

-- Metadata lookup for the trusted server; Storage schema stays unexposed.
create or replace function public.video_qa_storage_generation(
 p_owner uuid,p_path text
) returns uuid language plpgsql security invoker
set search_path='' as $
declare v_generation uuid;
begin
 if current_user not in ('postgres','service_role') then
  raise exception 'trusted role required';
 end if;
 if split_part(p_path,'/',1) <> p_owner::text then
  raise exception 'invalid owner path';
 end if;
 select s.id into v_generation from storage.objects s
 where s.bucket_id='post-videos' and s.name=p_path and s.owner_id=p_owner::text;
 return v_generation;
end $$;
revoke all on function public.video_qa_storage_generation(uuid,text)
 from public,anon,authenticated;
grant execute on function public.video_qa_storage_generation(uuid,text)
 to service_role;

-- ISOLATED SUPABASE QA ONLY. NEVER APPLY TO PRODUCTION.
-- PostgreSQL serializes concurrent publication by unique video_path.
-- Cleanup workers must reconcile posts by path before deleting any object.
alter table public.posts add column if not exists video_path text;
create unique index if not exists video_qa_posts_video_path_unique
  on public.posts (video_path) where video_path is not null;
create table if not exists public.video_cleanup_queue (
 id bigint generated always as identity primary key,
 object_path text not null unique,
 owner_id uuid not null,
 attempts integer not null default 0,
 next_attempt_at timestamptz not null default now(),
 created_at timestamptz not null default now(),
 last_error text,
 completed_at timestamptz
);
alter table public.video_cleanup_queue enable row level security;
revoke all on public.video_cleanup_queue from anon, authenticated;
-- No user-facing policy: only a reviewed trusted server can enqueue/claim.
create or replace function public.video_qa_publish(
 p_owner uuid, p_path text, p_content text
) returns uuid language plpgsql security invoker
set search_path = '' as $$
declare v_id uuid;
begin
 if p_path !~ '^[0-9a-f-]{36}/[0-9a-f-]{36}[.](mp4|webm)$'
    or split_part(p_path, '/', 1) <> p_owner::text then
   raise exception 'invalid video ownership';
 end if;
 insert into public.posts(user_id, content, image_urls, video_path)
 values (p_owner, p_content, '{}'::text[], p_path)
 on conflict (video_path) where video_path is not null do nothing
 returning id into v_id;
 if v_id is null then
   select id into v_id from public.posts
   where video_path = p_path and user_id = p_owner and content = p_content;
 end if;
 if v_id is null then raise exception 'video path already finalized with different content'; end if;
 return v_id;
end $$;
revoke all on function public.video_qa_publish(uuid,text,text) from public, anon, authenticated;
-- Trusted server may explicitly grant EXECUTE to its isolated server role.

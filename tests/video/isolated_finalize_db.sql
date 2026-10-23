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
 if current_user not in ('postgres', 'service_role') then
   raise exception 'trusted server role required';
 end if;
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

-- Isolated queue worker primitives. Transaction-scoped row locking prevents
-- concurrent claims; expired leases can be reclaimed after a crash.
alter table public.video_cleanup_queue
 add column if not exists lease_owner uuid,
 add column if not exists lease_until timestamptz;
create or replace function public.video_qa_claim_cleanup(p_worker uuid, p_lease_seconds integer default 60)
returns table(id bigint, owner_id uuid, object_path text, attempts integer)
language plpgsql security invoker set search_path = '' as $$
begin
 if current_user not in ('postgres', 'service_role') then
   raise exception 'trusted server role required';
 end if;
 if p_lease_seconds < 10 or p_lease_seconds > 600 then
   raise exception 'invalid lease duration';
 end if;
 return query
 with picked as (
  select q.id from public.video_cleanup_queue q
  where q.completed_at is null and q.next_attempt_at <= now()
    and (q.lease_until is null or q.lease_until < now())
  order by q.next_attempt_at, q.id
  for update skip locked limit 1
 )
 update public.video_cleanup_queue q
 set lease_owner=p_worker,
     lease_until=now() + make_interval(secs=>p_lease_seconds),
     attempts=q.attempts+1
 from picked where q.id=picked.id
 returning q.id,q.owner_id,q.object_path,q.attempts;
end $$;
revoke all on function public.video_qa_claim_cleanup(uuid,integer) from public, anon, authenticated;
create or replace function public.video_qa_finish_cleanup(
 p_id bigint,p_worker uuid,p_success boolean,p_reason text
) returns boolean language plpgsql security invoker set search_path = '' as $$
declare updated_count integer;
begin
 if current_user not in ('postgres','service_role') then
   raise exception 'trusted server role required';
 end if;
 update public.video_cleanup_queue q
 set completed_at=case when p_success then now() else null end,
     last_error=left(p_reason,500),
     next_attempt_at=case when p_success then q.next_attempt_at
       else now() + make_interval(secs=>least(3600,30 * (2 ^ least(q.attempts,7))::integer)) end,
     lease_owner=null,lease_until=null
 where q.id=p_id and q.lease_owner=p_worker and q.lease_until>now()
   and q.completed_at is null;
 get diagnostics updated_count = row_count;
 return updated_count=1;
end $$;
revoke all on function public.video_qa_finish_cleanup(bigint,uuid,boolean,text) from public, anon, authenticated;

-- Read-only reconciliation by owner and path. Use only after verifying
-- the caller's identity in a trusted server; never expose to client roles.
create or replace function public.video_qa_reconcile(
 p_owner uuid, p_path text
) returns uuid language plpgsql security invoker set search_path = '' as $$
declare v_id uuid;
begin
 if current_user not in ('postgres', 'service_role') then
   raise exception 'trusted server role required';
 end if;
 select p.id into v_id from public.posts p
 where p.user_id = p_owner and p.video_path = p_path;
 return v_id;
end $$;
revoke all on function public.video_qa_reconcile(uuid,text) from public,anon,authenticated;

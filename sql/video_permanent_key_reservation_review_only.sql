-- REVIEW ONLY / NOT APPLIED. Production key reservation candidate.
-- This ledger provides durable key non-reuse ONLY for writers that are
-- forced to reserve through this RPC. It does NOT by itself fence direct
-- Supabase Storage uploads, service_role, owner UPDATE/DELETE, or Storage
-- administrator writes. Keep VIDEO_PRODUCTION_FENCED_READY disabled.
--
-- The reservation must never be deleted, even after a post or Storage object
-- is removed. Upload orchestration must call this BEFORE any Storage write;
-- all other write paths must be independently prohibited and audited.
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
  from public, anon, authenticated;
-- Read-only owner predicate for a future Storage INSERT policy.
-- SECURITY DEFINER bypasses ledger RLS without exposing the ledger itself.
-- Only the exact authenticated owner and reserved path may match.
create or replace function public.video_reserved_key_is_owned(
  p_path text, p_owner uuid
) returns boolean language sql stable security definer
set search_path = '' as $
  select p_owner is not null
    and p_owner = (select auth.uid())
    and exists (
      select 1 from public.video_reserved_object_keys r
      where r.bucket_id = 'post-videos'
        and r.object_path = p_path
        and r.owner_id = p_owner
    );
$;
revoke all on function public.video_reserved_key_is_owned(text,uuid)
  from public, anon;
grant execute on function public.video_reserved_key_is_owned(text,uuid)
  to authenticated;
-- This helper is a prerequisite only; it does not fence permissive INSERT
-- policies, privileged service_role Storage writes, or upserts.

-- Trusted service-role EXECUTE grant is a separate audited release step.
-- SECURITY BLOCKER: reservation must be transactionally bound to all upload
-- paths, including retries; Storage is a separate service so DB uniqueness
-- alone cannot make its write atomic with this reservation.
-- Never apply this script without privilege, search_path, role, and
-- Storage policy review and isolated Postgres/Storage integration tests.

-- GENERAL PUBLIC VIDEO ROLLOUT CANDIDATE — NOT AUTHORIZED FOR PRODUCTION.
-- Apply only after the existing testplayer-limited migration has been reviewed.
-- Does not change existing posts, Storage files, or existing allowed_publishers.
-- Fully additive except for replacing the existing membership RPC's definition.
-- Initially OFF. Emergency video_private.rollout_settings.enabled remains authoritative.
begin;
do $guard$
begin
  if to_regclass('video_private.rollout_settings') is null
     or to_regclass('video_private.allowed_publishers') is null
     or to_regprocedure('public.video_rollout_member()') is null then
    raise exception 'limited video rollout must be installed first';
  end if;
end
$guard$;

create table if not exists video_private.general_public_rollout (
  singleton boolean primary key default true check (singleton),
  enabled boolean not null default false
);
revoke all on video_private.general_public_rollout from public,anon,authenticated,service_role;
insert into video_private.general_public_rollout(singleton,enabled)
  values(true,false) on conflict(singleton) do nothing;

-- Membership uses the caller's verified JWT identity and an unexpired JWT.
-- No user_metadata, display name, client flag, or untrusted owner ID can grant access.
-- The separate production rollout_settings.enabled gate still controls mutation.
create or replace function public.video_rollout_member() returns boolean
language sql volatile security definer set search_path='' as $member$
  select
    case when coalesce(nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'exp','') ~ '^[0-9]{1,12}$'
      then (nullif(current_setting('request.jwt.claims',true),'')::jsonb->>'exp')::bigint > extract(epoch from clock_timestamp())
      else false end
    and auth.uid() is not null
    and (
      exists(select 1 from video_private.allowed_publishers
             where user_id=auth.uid() and enabled)
      or exists(select 1 from video_private.general_public_rollout
                where singleton and enabled)
    );
$member$;
revoke all on function public.video_rollout_member() from public,anon,service_role;
grant execute on function public.video_rollout_member() to authenticated;
-- Activation must be an explicit, separately approved operator transaction:
-- UPDATE video_private.general_public_rollout SET enabled=true WHERE singleton=true;
-- Revoke access by setting enabled=false. Preserve limited rollout and global
-- emergency stop settings. No destructive rollback.
commit;

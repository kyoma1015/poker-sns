-- Dedicated Poker ID video TEST project only. Install only on hbhyuotzginwysrineyo.
-- Read-only proof: an expired owner reservation exists and no post was published.
create or replace function public.video_cloud_expired_unpublished(p_path text)
returns boolean language plpgsql security definer set search_path='' as $$
declare v_owner uuid := auth.uid(); v_expired boolean;
begin
 if v_owner is null or not public.video_cloud_allowed() then return false; end if;
 if p_path is null or p_path !~ ('^'||v_owner::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm|mov)$') then return false; end if;
 select r.expires_at <= clock_timestamp() into v_expired
 from video_cloud.reservations r where r.path=p_path and r.owner_id=v_owner;
 if v_expired is distinct from true then return false; end if;
 if exists(select 1 from public.posts p where p.video_path=p_path) then return false; end if;
 return true;
end $$;
revoke all on function public.video_cloud_expired_unpublished(text) from public,anon,service_role;
grant execute on function public.video_cloud_expired_unpublished(text) to authenticated;

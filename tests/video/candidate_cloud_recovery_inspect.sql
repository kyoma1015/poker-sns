-- CANDIDATE ONLY. Apply to isolated video-test DB after security review.
-- Owner-scoped, read-only classification of expired or live reservations.
-- Never deletes, resumes, republishes, or authorizes a new upload.
create or replace function public.video_cloud_recovery_inspect_v1(p_path text)
returns jsonb language plpgsql security definer set search_path = ''
as $$
declare
  v_owner uuid := auth.uid();
  v_res video_cloud.reservations%rowtype;
  v_object storage.objects%rowtype;
  v_post public.posts%rowtype;
begin
  if v_owner is null or not public.video_cloud_allowed() then raise exception 'denied'; end if;
  if p_path is null or p_path !~ ('^'||v_owner::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm|mov)$') then
    raise exception 'invalid path';
  end if;
  select * into v_res from video_cloud.reservations
   where path=p_path and owner_id=v_owner;
  if not found then raise exception 'reservation not found'; end if;
  select * into v_object from storage.objects
   where bucket_id='post-videos' and name=p_path and owner_id=v_owner::text;
  select * into v_post from public.posts
   where video_path=p_path and user_id=v_owner;
  if v_post.id is not null and (
     v_object.id is null or v_post.video_generation is distinct from v_object.id
     or v_post.video_sha256 is distinct from v_res.sha256
  ) then
    return jsonb_build_object('state','conflict','allow_resume',false,'path',p_path);
  end if;
  return jsonb_build_object(
    'state',case
      when v_post.id is not null then 'published'
      when v_object.id is not null then 'stored_unpublished'
      when v_res.expires_at<=clock_timestamp() then 'expired_empty'
      else 'reserved_empty' end,
    'allow_resume',false,
    'expired',v_res.expires_at<=clock_timestamp(),
    'path',p_path,
    'post_id',v_post.id,
    'sha256',v_res.sha256,
    'size',v_res.size,
    'storage_present',v_object.id is not null
  );
end $$;
revoke all on function public.video_cloud_recovery_inspect_v1(text) from public, anon;
grant execute on function public.video_cloud_recovery_inspect_v1(text) to authenticated;

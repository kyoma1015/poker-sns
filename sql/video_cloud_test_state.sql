-- Dedicated test project only; run after foundation and publish migrations.
begin;
do $$ begin
 if current_setting('video.cloud_test_project_ref',true) is distinct from 'hbhyuotzginwysrineyo' then raise exception 'test target required'; end if;
end $$;
create function public.video_cloud_state(p_path text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r video_cloud.reservations%rowtype; g uuid;
begin
 if not public.video_cloud_allowed() then raise exception 'denied'; end if;
 select * into r from video_cloud.reservations where path=p_path and owner_id=auth.uid();
 if not found or r.expires_at<=clock_timestamp() then raise exception 'expired'; end if;
 select id into g from storage.objects where bucket_id='post-videos' and name=p_path and owner_id=auth.uid()::text;
 if g is null then raise exception 'missing object'; end if;
 return jsonb_build_object('sha256',r.sha256,'size',r.size,'mime',r.mime,'content',r.content,'generation',g);
end $$;
revoke all on function public.video_cloud_state(text) from public,anon,service_role;
grant execute on function public.video_cloud_state(text) to authenticated;
commit;

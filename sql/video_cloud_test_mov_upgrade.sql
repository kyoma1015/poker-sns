-- Dedicated isolated cloud-video test project only. Never apply to production.
-- Allows QuickTime MOV without weakening 20 MiB, 30 s, JWT or Storage ownership guards.
begin;
do $guard$
begin
 if current_setting('video.cloud_test_project_ref', true) is distinct from 'hbhyuotzginwysrineyo'
 then raise exception 'dedicated test target required'; end if;
 if not exists (select 1 from storage.buckets where id='post-videos' and public=false)
 then raise exception 'private video bucket unavailable'; end if;
end
$guard$;

alter table video_cloud.reservations
 drop constraint reservations_mime_check,
 add constraint reservations_mime_check check (mime in ('video/mp4','video/webm','video/quicktime')),
 drop constraint reservations_check,
 add constraint reservations_check check (path ~ ('^'||owner_id::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm|mov)$')),
 drop constraint reservations_check1,
 add constraint reservations_check1 check ((mime='video/mp4' and path like '%.mp4') or (mime='video/webm' and path like '%.webm') or (mime='video/quicktime' and path like '%.mov'));

alter table public.posts
 drop constraint posts_check,
 add constraint posts_check check (video_path ~ ('^'||user_id::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm|mov)$'));

update storage.buckets
 set allowed_mime_types = array['video/mp4','video/webm','video/quicktime']
 where id='post-videos' and public=false and file_size_limit=20971520;

do $rpc$
declare old_def text; new_def text;
begin
 old_def := pg_get_functiondef('public.video_cloud_publish_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)'::regprocedure);
 if strpos(old_def, '(mp4|webm)')=0 then raise exception 'unexpected existing publish RPC'; end if;
 new_def := replace(old_def, '(mp4|webm)', '(mp4|webm|mov)');
 execute new_def;
end
$rpc$;
commit;
-- Execute after applying candidate SQL in disposable postgres.
\set ON_ERROR_STOP on
insert into public.posts(id,user_id,image_urls) values
 ('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','{}');
do $$begin
 if (select public from storage.buckets where id='post-videos') is distinct from false then raise exception 'bucket not private'; end if;
 if (select file_size_limit from storage.buckets where id='post-videos') <> 20971520 then raise exception 'size limit mismatch'; end if;
 if (select count(*) from pg_policies where schemaname='storage' and tablename='objects' and policyname like 'post_videos_%') <> 3 then raise exception 'unexpected video policy count'; end if;
end$$;
-- Reject mixed image/video posts at the SQL constraint boundary.
do $qa$begin
 begin
  update public.posts set image_urls=array['image.jpg'],
   video_path='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4'
   where id='20000000-0000-0000-0000-000000000001';
  raise exception 'mixed image/video accepted';
 exception when check_violation then null;
 end;
end$qa$;
-- Reject malformed video path.
do $qa$begin
 begin
  update public.posts set video_path='../other.mp4'
   where id='20000000-0000-0000-0000-000000000001';
  raise exception 'invalid path accepted';
 exception when check_violation then null;
 end;
end$qa$;
-- Confirm the allowed path is accepted.
update public.posts set video_path='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4'
 where id='20000000-0000-0000-0000-000000000001';
set role video_owner;
set request.jwt.claim.sub='10000000-0000-0000-0000-000000000001';
insert into storage.objects(bucket_id,name,owner_id) values('post-videos','10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4','10000000-0000-0000-0000-000000000001');
do $$begin if (select count(*) from storage.objects where bucket_id='post-videos')<>1 then raise exception 'owner cannot read'; end if; end$$;
reset role;
set role video_viewer;
set request.jwt.claim.sub='10000000-0000-0000-0000-000000000002';
do $$begin if exists(select 1 from storage.objects where bucket_id='post-videos') then raise exception 'non-owner can read'; end if; end$$;
-- Non-owner INSERT must be rejected by Storage RLS.
do $qa$begin
 begin
  insert into storage.objects(bucket_id,name,owner_id)
  values ('post-videos','10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000002.mp4','10000000-0000-0000-0000-000000000002');
  raise exception 'non-owner insert accepted';
 exception when insufficient_privilege then null;
 end;
end$qa$;
-- Non-owner DELETE must not affect the owner's row.
delete from storage.objects where bucket_id='post-videos';
do $qa$begin
 if (select count(*) from storage.objects where bucket_id='post-videos')<>0 then
  raise exception 'viewer unexpectedly sees owner row';
 end if;
end$qa$;
reset role;
set role video_owner;
set request.jwt.claim.sub='10000000-0000-0000-0000-000000000001';
delete from storage.objects where bucket_id='post-videos';
do $$begin if exists(select 1 from storage.objects where bucket_id='post-videos') then raise exception 'owner delete failed'; end if; end$$;
reset role;

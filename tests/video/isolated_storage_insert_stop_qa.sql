-- DISPOSABLE LOCAL SUPABASE ONLY. Execute after all other isolated Storage E2E.
-- This creates a deliberately permissive legacy INSERT path to reproduce
-- the OR-policy bypass, then proves a RESTRICTIVE policy stops it.
\set ON_ERROR_STOP on
create or replace function public.video_rollout_allowed()
returns boolean language sql stable security invoker set search_path=''
as $$ select current_setting('video.qa_rollout',true) = 'on' $$;
create policy video_qa_legacy_permissive_insert on storage.objects
  for insert to authenticated with check (
    (bucket_id='post-videos' and name like '11111111-1111-4111-8111-111111111111/%')
    or bucket_id='video-qa-unrelated'
  );
insert into storage.buckets(id,name,public)
values ('video-qa-unrelated','video-qa-unrelated',false)
on conflict (id) do nothing;
\echo 'QA: apply restrictive candidate first time'
\ir production_storage_insert_stop_NOT_APPROVED.sql
\echo 'QA: reapply restrictive candidate unchanged'
\ir production_storage_insert_stop_NOT_APPROVED.sql
do $$
begin
 if not exists (select 1 from pg_policies where schemaname='storage'
   and tablename='objects' and policyname='video_recovery_restrict_video_bucket_insert'
   and permissive='RESTRICTIVE' and cmd='INSERT')
 then raise exception 'restrictive policy not installed'; end if;
end $$;
-- Test INSERTs are rolled back, leaving no persistent QA Storage rows.
begin;
set local role authenticated;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true);
select set_config('video.qa_rollout','off',true);
do $$
begin
 begin
   insert into storage.objects(bucket_id,name,owner_id)
   values('post-videos','11111111-1111-4111-8111-111111111111/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa.mp4',
          '11111111-1111-4111-8111-111111111111');
   raise exception 'FAIL: video insert succeeded with rollout disabled';
 exception when insufficient_privilege then
   raise notice 'PASS: existing-reservation-equivalent legacy video insert denied with rollout off';
 end;
end $$;
insert into storage.objects(bucket_id,name,owner_id)
values('video-qa-unrelated','qa-object','11111111-1111-4111-8111-111111111111');
select set_config('video.qa_rollout','on',true);
insert into storage.objects(bucket_id,name,owner_id)
values('post-videos','11111111-1111-4111-8111-111111111111/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb.mp4',
       '11111111-1111-4111-8111-111111111111');
rollback;
\echo 'PASS: rollout off denies video; nonvideo and rollout-on video allowed'
-- A different policy definition with the same name must not be silently replaced.
alter policy video_recovery_restrict_video_bucket_insert on storage.objects
 with check (true);
\set ON_ERROR_STOP off
\set QUIET on
\o /dev/null
\ir production_storage_insert_stop_NOT_APPROVED.sql
\o
\set QUIET off
\set ON_ERROR_STOP on
do $$
begin
 if not exists(select 1 from pg_policies where schemaname='storage'
   and tablename='objects' and policyname='video_recovery_restrict_video_bucket_insert'
   and with_check='true')
 then raise exception 'FAIL: modified policy was overwritten'; end if;
end $$;
\echo 'PASS: drifted restrictive policy not overwritten (review failure output above)'

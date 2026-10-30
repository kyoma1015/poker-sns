-- Disposable PostgreSQL fixture only. DO NOT APPLY TO PRODUCTION.
-- Run after existing candidate-policy assertions, which deliberately test DELETE.
\set ON_ERROR_STOP on
drop policy if exists post_videos_delete_own on storage.objects;
revoke update, delete on storage.objects from authenticated;
-- A real Supabase Storage installation already enforces unique(bucket_id,name).
create unique index if not exists isolated_storage_bucket_name_unique
  on storage.objects(bucket_id,name);
-- Confirm every remaining permissive mutation policy for this fixture.
do $$
begin
 if exists (
   select 1 from pg_policies
   where schemaname='storage' and tablename='objects'
     and cmd in ('UPDATE','DELETE','ALL')
 ) then raise exception 'mutation policy remains on immutable fixture'; end if;
end $$;

-- Role with an owner-scoped INSERT policy can insert a new UUID key once.
set role video_owner;
select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000001',false);
insert into storage.objects(bucket_id,name,owner_id)
values ('post-videos',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4',
 '10000000-0000-0000-0000-000000000001');
-- A duplicate path must fail at the unique index even if INSERT is allowed.
do $$
begin
 begin
   insert into storage.objects(bucket_id,name,owner_id)
   values ('post-videos',
    '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4',
    '10000000-0000-0000-0000-000000000001');
   raise exception 'duplicate insert unexpectedly succeeded';
 exception when unique_violation then null;
 end;
end $$;
-- Role cannot UPDATE or DELETE any Storage object.
do $$
begin
 begin
   delete from storage.objects where bucket_id='post-videos';
   raise exception 'immutable delete unexpectedly succeeded';
 exception when insufficient_privilege then null;
 end;
 begin
   update storage.objects set name='replacement' where bucket_id='post-videos';
   raise exception 'immutable update unexpectedly succeeded';
 exception when insufficient_privilege then null;
 end;
end $$;
reset role;
select 'PASS: isolated insert-once Storage and denied UPDATE/DELETE' as result;

-- Disposable fixture only, after production_additive_candidate.sql.
\set ON_ERROR_STOP on
do $$
begin
 if (select count(*) from public.posts where content='preserved existing post')<>1 then
  raise exception 'existing post was modified or lost';
 end if;
 if not exists(select 1 from storage.buckets where id='post-videos' and public=false) then
  raise exception 'private bucket missing';
 end if;
 if exists(select 1 from pg_policies where schemaname='storage' and tablename='objects'
   and cmd in ('UPDATE','DELETE','ALL') and
   (coalesce(qual,'') ilike '%post-videos%' or coalesce(with_check,'') ilike '%post-videos%'))
 then raise exception 'video mutation policy exists'; end if;
end $$;
-- Verify real client roles cannot execute the privileged RPCs.
set role authenticated;
do $client_grants$
begin
 if has_function_privilege(current_user, 'public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text)','EXECUTE')
 or has_function_privilege(current_user, 'public.video_production_storage_generation(uuid,text)','EXECUTE')
 or has_function_privilege(current_user, 'public.video_production_reconcile_fenced(uuid,text,uuid)','EXECUTE')
 then raise exception 'authenticated role can execute privileged video RPC'; end if;
end $client_grants$;
reset role;
-- Service RPC must not be executable by regular authenticated users.
set role video_owner;
do $$
begin
 if has_function_privilege(current_user,
 'public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text)','EXECUTE')
 then raise exception 'client can call privileged publish RPC'; end if;
end $$;
reset role;
-- Exercise idempotency, owner, generation and payload fencing as the actual service_role.
insert into storage.objects(id,bucket_id,name,owner_id) values
 ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','post-videos',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm',
 '10000000-0000-0000-0000-000000000001');
set role service_role;
do $service_privileges$
begin
 if not has_table_privilege(current_user,'public.posts','SELECT') or not has_table_privilege(current_user,'public.posts','INSERT')
 or not has_table_privilege(current_user,'storage.objects','SELECT')
 or not has_table_privilege(current_user,'storage.objects','UPDATE') then
 raise exception 'service_role posts privilege mismatch'; end if;
end $service_privileges$;
do $service_test$
declare
 a uuid; b uuid;
 p text:='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm';
begin
 a:=public.video_production_publish_fenced('10000000-0000-0000-0000-000000000001',p,
 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',repeat('a',64),2,'hello');
 b:=public.video_production_publish_fenced('10000000-0000-0000-0000-000000000001',p,
 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',repeat('a',64),2,'hello');
 if a<>b then raise exception 'idempotency failure'; end if;
 if public.video_production_reconcile_fenced('10000000-0000-0000-0000-000000000001',p,
 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa')<>a then raise exception 'reconcile failure'; end if;
 begin
 perform public.video_production_publish_fenced('10000000-0000-0000-0000-000000000001',p,
 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',repeat('a',64),2,'hello');
 raise exception 'wrong generation accepted';
 exception when raise_exception then
  if sqlerrm='wrong generation accepted' then raise; end if;
 end;
 begin
 perform public.video_production_publish_fenced('10000000-0000-0000-0000-000000000001',p,
 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',repeat('a',64),2,'changed');
 raise exception 'conflicting replay accepted';
 exception when raise_exception then
  if sqlerrm='conflicting replay accepted' then raise; end if;
 end;
end $service_test$;
reset role;
select 'PASS: production candidate isolated preservation, private bucket, RPC grants, generation and replay' as result;

-- SECURITY REGRESSION: even a permanent reservation + authenticated INSERT RLS
-- cannot prevent service_role from directly mutating Storage objects.
-- This is a release blocker, not a passing writer-fence assertion.
do $privileged_writer_audit$
begin
 if not (select rolbypassrls from pg_roles where rolname='service_role') then
  raise exception 'test fixture does not model production service_role BYPASSRLS';
 end if;
 if not has_table_privilege('service_role','storage.objects','INSERT')
    or not has_table_privilege('service_role','storage.objects','UPDATE') then
  raise exception 'test fixture does not model privileged Storage writer';
 end if;
 raise notice 'RELEASE BLOCKER: privileged service_role can bypass authenticated reservation policy; end-to-end writer fence not proven';
end $privileged_writer_audit$;

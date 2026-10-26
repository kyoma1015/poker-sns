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
-- JWT-scoped SECURITY DEFINER RPCs: verify grants and owner fencing.
set role authenticated;
do $client_grants$
begin
 if not has_function_privilege(current_user,'public.video_production_publish_fenced(uuid,text,uuid,text,double precision,text)','EXECUTE')
 or not has_function_privilege(current_user,'public.video_production_storage_generation(uuid,text)','EXECUTE')
 or not has_function_privilege(current_user,'public.video_production_reconcile_fenced(uuid,text,uuid)','EXECUTE')
 then raise exception 'authenticated owner RPC grant missing'; end if;
end $client_grants$;
reset role;
insert into storage.objects(id,bucket_id,name,owner_id) values
 ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa','post-videos',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm',
 '10000000-0000-0000-0000-000000000001'),
 ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','post-videos',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000002.webm',
 '10000000-0000-0000-0000-000000000001');
set role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000001',false);
do $owner_test$
declare
 a uuid; b uuid;
 p text:='10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm';
begin
 if public.video_production_storage_generation('10000000-0000-0000-0000-000000000001',p)
    <> 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::uuid then raise exception 'generation mismatch'; end if;
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
end $owner_test$;
select set_config('request.jwt.claim.sub','20000000-0000-0000-0000-000000000002',false);
do $foreign_owner$
begin
 begin
 perform public.video_production_storage_generation('10000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm');
 raise exception 'foreign generation accepted';
 exception when raise_exception then
  if sqlerrm='foreign generation accepted' then raise; end if;
 end;
 begin
 perform public.video_production_publish_fenced('10000000-0000-0000-0000-000000000001',
 '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.webm',
 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',repeat('a',64),2,'hello');
 raise exception 'foreign publish accepted';
 exception when raise_exception then
  if sqlerrm='foreign publish accepted' then raise; end if;
 end;
end $foreign_owner$;
reset role;
select 'PASS: owner JWT fenced publication, idempotency, foreign denial' as result;
-- SECURITY REGRESSION: an authenticated owner must NOT be able to forge
-- server-only ffprobe evidence and directly publish an uninspected object.
-- This must fail until the RPC verifies an unforgeable server attestation.
set role authenticated;
select set_config('request.jwt.claim.sub','10000000-0000-0000-0000-000000000001',false);
do $untrusted_metadata_gate$
declare forged uuid;
begin
 begin
  forged := public.video_production_publish_fenced(
   '10000000-0000-0000-0000-000000000001',
   '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000002.webm',
   'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',repeat('b',64),29.9,
   'forged unverified ffprobe metadata');
 exception when others then
  return;
 end;
 raise exception 'NO-GO: owner JWT can publish without server ffprobe attestation';
end $untrusted_metadata_gate$;
reset role;


-- SECURITY REGRESSION: even a permanent reservation + authenticated INSERT RLS
-- cannot prevent service_role from directly mutating Storage objects.
-- This is a release blocker, not a passing writer-fence assertion.
do $privileged_writer_audit$
begin
 if not (select rolbypassrls from pg_roles where rolname='service_role') then
  raise exception 'test fixture does not model production service_role BYPASSRLS';
 end if;
 -- Disposable PostgreSQL fixture does not grant the full Supabase Storage
 -- service_role privilege set. Never mistake this for a production writer fence.
 if not has_table_privilege('service_role','storage.objects','INSERT')
    or not has_table_privilege('service_role','storage.objects','UPDATE') then
  raise notice 'ISOLATED FIXTURE LIMITATION: service_role Storage mutation grants differ from live Supabase';
 end if;
 raise notice 'RELEASE BLOCKER: privileged service_role can bypass authenticated reservation policy; end-to-end writer fence not proven';
end $privileged_writer_audit$;

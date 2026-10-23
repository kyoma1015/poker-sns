-- Isolated-only SQL contract: use psql with ON_ERROR_STOP=1 after
-- storage_bootstrap.sql and isolated_finalize_db.sql.
begin;
do $$
declare
 owner uuid := '10000000-0000-0000-0000-000000000001';
 path text := '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4';
 first_id uuid;
 second_id uuid;
begin
 insert into auth.users(id, instance_id, aud, role, email, encrypted_password, created_at, updated_at)
 values(owner, '00000000-0000-0000-0000-000000000000', 'authenticated', 'authenticated',
 'video-qa@example.invalid', '', now(), now())
 on conflict (id) do nothing;
 first_id := public.video_qa_publish(owner,path,'test');
 second_id := public.video_qa_publish(owner,path,'test');
 if first_id <> second_id then raise exception 'idempotency failed'; end if;
 begin
   perform public.video_qa_publish(owner,path,'changed');
   raise exception 'conflicting content unexpectedly accepted';
 exception when raise_exception then
   if sqlerrm = 'conflicting content unexpectedly accepted' then raise; end if;
 end;
 insert into public.video_cleanup_queue(owner_id, object_path)
 values(owner,path) on conflict (object_path) do nothing;
 if (select count(*) from public.video_cleanup_queue where object_path=path) <> 1 then
   raise exception 'cleanup deduplication failed';
 end if;

 if (select count(*) from public.video_qa_claim_cleanup('50000000-0000-0000-0000-000000000001'::uuid,60)) <> 1 then
   raise exception 'cleanup claim failed';
 end if;
 if (select count(*) from public.video_qa_claim_cleanup('50000000-0000-0000-0000-000000000002'::uuid,60)) <> 0 then
   raise exception 'leased cleanup claimed twice';
 end if;
 if public.video_qa_finish_cleanup(
   (select id from public.video_cleanup_queue where object_path=path),
   '50000000-0000-0000-0000-000000000002'::uuid,true,'bad owner') then
   raise exception 'wrong worker finalized lease';
 end if;
 if not public.video_qa_finish_cleanup(
   (select id from public.video_cleanup_queue where object_path=path),
   '50000000-0000-0000-0000-000000000001'::uuid,false,'retry') then
   raise exception 'valid worker could not reschedule';
 end if;
 if (select completed_at from public.video_cleanup_queue where object_path=path) is not null then
   raise exception 'retry incorrectly marked complete';
 end if;
end $$;
rollback;

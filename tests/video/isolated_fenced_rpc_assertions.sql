-- Disposable PostgreSQL-only RPC fixture, after isolated_insert_once_storage.sql.
\set ON_ERROR_STOP on
do $$ begin
 if not exists(select 1 from pg_roles where rolname='service_role') then
  create role service_role nologin;
 end if;
end $$;
alter table public.posts add column if not exists content text not null default '';
alter table public.posts alter column id set default gen_random_uuid();
create unique index if not exists video_qa_posts_video_path_unique
 on public.posts(video_path) where video_path is not null;
\i tests/video/isolated_fenced_publish.sql
do $$
declare
 owner uuid := '10000000-0000-0000-0000-000000000001';
 path text := '10000000-0000-0000-0000-000000000001/30000000-0000-0000-0000-000000000001.mp4';
 gen uuid;
 first_id uuid;
 second_id uuid;
begin
 select id into gen from storage.objects where bucket_id='post-videos' and name=path;
 if gen is null then raise exception 'Storage fixture object missing'; end if;
 if public.video_qa_storage_generation(owner,path) is distinct from gen then
  raise exception 'generation metadata mismatch';
 end if;
 begin
  perform public.video_qa_publish_fenced(owner,path,gen_random_uuid(),repeat('a',64),2,'hello');
  raise exception 'incorrect generation accepted';
 exception when raise_exception then
  if sqlerrm='incorrect generation accepted' then raise; end if;
 end;
 first_id := public.video_qa_publish_fenced(owner,path,gen,repeat('a',64),2,'hello');
 second_id := public.video_qa_publish_fenced(owner,path,gen,repeat('a',64),2,'hello');
 if first_id is null or first_id is distinct from second_id then
  raise exception 'idempotent publish failed';
 end if;
 if public.video_qa_reconcile_fenced(owner,path,gen) is distinct from first_id then
  raise exception 'generation reconciliation failed';
 end if;
 if public.video_qa_reconcile_fenced(owner,path,gen_random_uuid()) is not null then
  raise exception 'ABA generation mismatch incorrectly reconciled';
 end if;
 begin
  perform public.video_qa_publish_fenced(owner,path,gen,repeat('b',64),2,'different');
  raise exception 'conflicting content accepted';
 exception when raise_exception then
  if sqlerrm='conflicting content accepted' then raise; end if;
 end;
end $$;
select 'PASS: actual PostgreSQL fenced RPC, generation mismatch, idempotency, reconciliation' as result;

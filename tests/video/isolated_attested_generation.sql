-- DISPOSABLE LOCAL SUPABASE ONLY. Owner-scoped generation lookup used by
-- the production candidate adapter; do not apply this fixture to production.
create or replace function public.video_production_storage_generation(p_owner uuid,p_path text)
returns uuid language plpgsql security definer set search_path='' as $$
declare v uuid;
begin
 if (select auth.uid()) is distinct from p_owner or
  split_part(p_path,'/',1)<>p_owner::text then raise exception 'trusted owner required'; end if;
 select id into v from storage.objects where bucket_id='post-videos' and name=p_path
  and owner_id=p_owner::text;
 return v;
end $$;
revoke all on function public.video_production_storage_generation(uuid,text) from public,anon,service_role;
grant execute on function public.video_production_storage_generation(uuid,text) to authenticated;

-- Align the disposable posts table with the production candidate INSERT shape.
-- The isolated seed intentionally omits these application columns.
alter table public.posts add column if not exists post_type text not null default 'normal';

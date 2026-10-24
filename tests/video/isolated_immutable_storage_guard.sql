"""Isolated-only immutable Storage RLS test: no owner UPDATE/DELETE.

This fixture is applied only to a fresh local Supabase stack, after removing
the QA DELETE grant. Never run against production.
"""
drop policy if exists "post_videos_delete_own" on storage.objects;
drop policy if exists "post_videos_update_own" on storage.objects;
-- QA read and insert policies remain, so uploads/downloads still work.
-- No UPDATE or DELETE grants should remain for authenticated users.
do $$
begin
  if exists (
    select 1 from pg_policies
    where schemaname='storage' and tablename='objects'
      and cmd in ('UPDATE','DELETE','ALL')
      and (roles @> array['authenticated']::name[] or roles @> array['public']::name[])
      and (qual ilike '%post-videos%' or with_check ilike '%post-videos%')
  ) then
    raise exception 'unsafe Storage policy grants update/delete on post-videos';
  end if;
end $$;

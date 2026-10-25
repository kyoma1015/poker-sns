-- Disposable Supabase stack only. Apply AFTER legacy Storage QA tests.
-- The old permissive INSERT policy must never coexist with the reservation fence.
drop policy if exists "post_videos_insert_own" on storage.objects;
do $$
declare p record;
begin
  for p in select * from pg_policies
    where schemaname='storage' and tablename='objects'
      and cmd in ('INSERT','ALL') and permissive='PERMISSIVE'
      and (roles @> array['authenticated']::name[]
        or roles @> array['public']::name[])
  loop
    if p.policyname <> 'post_videos_immutable_insert_own' then
      -- Fail closed even for generic policies: their OR semantics can bypass
      -- bucket-scoped reservations. Review rather than guessing equivalence.
      raise exception 'unreviewed permissive Storage writer policy: %', p.policyname;
    end if;
  end loop;
  for p in select * from pg_policies
    where schemaname='storage' and tablename='objects'
      and cmd in ('UPDATE','DELETE','ALL') and permissive='PERMISSIVE'
      and (roles @> array['authenticated']::name[]
        or roles @> array['public']::name[])
  loop
    raise exception 'unreviewed mutating Storage writer policy: %', p.policyname;
  end loop;
  if not exists (
    select 1 from pg_policies
    where schemaname='storage' and tablename='objects'
      and policyname='post_videos_immutable_insert_own'
      and with_check like '%video_reserved_key_is_owned%'
  ) then
    raise exception 'reservation-enforced INSERT policy missing';
  end if;
end $$;

-- Run once in Supabase SQL Editor. Private PNG storage for exact Poker ID card OG previews.
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types)
values ('poker-id-card-og','poker-id-card-og',false,5242880,array['image/png'])
on conflict(id) do nothing;

do $$
begin
  if not exists (select 1 from pg_policies where schemaname='storage' and tablename='objects' and policyname='Owner uploads poker ID OG') then
    create policy "Owner uploads poker ID OG" on storage.objects for insert to authenticated
    with check (bucket_id='poker-id-card-og' and (storage.foldername(name))[1]=auth.uid()::text);
  end if;
  if not exists (select 1 from pg_policies where schemaname='storage' and tablename='objects' and policyname='Owner updates poker ID OG') then
    create policy "Owner updates poker ID OG" on storage.objects for update to authenticated
    using (bucket_id='poker-id-card-og' and (storage.foldername(name))[1]=auth.uid()::text)
    with check (bucket_id='poker-id-card-og' and (storage.foldername(name))[1]=auth.uid()::text);
  end if;
  if not exists (select 1 from pg_policies where schemaname='storage' and tablename='objects' and policyname='Owner reads poker ID OG') then
    create policy "Owner reads poker ID OG" on storage.objects for select to authenticated
    using (bucket_id='poker-id-card-og' and (storage.foldername(name))[1]=auth.uid()::text);
  end if;
end $$;

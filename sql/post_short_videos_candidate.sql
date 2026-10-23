-- REVIEW ONLY. NOT FOR PRODUCTION EXECUTION WITHOUT SEPARATE APPROVAL.
-- The existing posts table is assumed to have id and user_id.
-- Storage policies must be reconciled with existing policies before application.
alter table public.posts add column if not exists video_url text;
alter table public.posts add constraint posts_video_or_images_exclusive
  check (video_url is null or coalesce(cardinality(image_urls), 0) = 0);
-- Create a private storage bucket, max 20 MiB, only MP4/WebM.
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('post-videos', 'post-videos', false, 20971520, array['video/mp4','video/webm'])
on conflict (id) do nothing;
-- Path contract: <auth.uid()>/<random-uuid>.mp4 or .webm
create policy "post_videos_insert_own" on storage.objects for insert to authenticated
with check (bucket_id = 'post-videos' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "post_videos_select_own" on storage.objects for select to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "post_videos_delete_own" on storage.objects for delete to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = auth.uid()::text);
-- Private playback requires a separately reviewed signed-URL delivery path.
-- Client-side duration checks are NOT a security boundary; add server validation.

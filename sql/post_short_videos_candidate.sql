-- REVIEW ONLY. DO NOT APPLY TO PRODUCTION.
-- posts schema confirmed read-only: id uuid, user_id uuid, image_urls text[].
-- This is a draft, not an executable migration. Server-side 30s validation is BLOCKED.
alter table public.posts add column if not exists video_path text;
alter table public.posts add constraint posts_video_path_valid
  check (video_path is null or video_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}[.](mp4|webm)$');
alter table public.posts add constraint posts_video_or_images_exclusive
  check (video_path is null or coalesce(cardinality(image_urls), 0) = 0);

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('post-videos', 'post-videos', false, 20971520, array['video/mp4','video/webm'])
on conflict (id) do nothing;

create policy "post_videos_insert_own" on storage.objects for insert to authenticated
with check (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "post_videos_read_own" on storage.objects for select to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "post_videos_delete_own" on storage.objects for delete to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);

-- BLOCKED: non-owner playback must not be enabled until reviewed RLS and signed URL delivery.
-- BLOCKED: 30s duration cannot be enforced by MIME or file size alone.
-- BLOCKED: full video publish and orphan cleanup need isolated E2E verification.

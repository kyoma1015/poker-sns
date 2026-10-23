-- REVIEW ONLY: DO NOT EXECUTE ON PRODUCTION.
-- Assumes posts(id uuid, user_id uuid, image_urls text[]). Confirmed by read-only catalog.
-- Server-side duration validation and deletion lifecycle must be designed before activation.
alter table public.posts add column if not exists video_path text;
-- Keep image/video mutually exclusive. Review existing constraints before applying.
alter table public.posts add constraint posts_video_path_valid
  check (video_path is null or video_path ~ '^[0-9a-f-]{36}/[0-9a-f-]{36}[.](mp4|webm));
alter table public.posts add constraint posts_video_or_images_exclusive
  check (video_path is null or coalesce(cardinality(image_urls), 0) = 0);
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('post-videos', 'post-videos', false, 20971520, array['video/mp4','video/webm'])
on conflict (id) do nothing;
-- Owners can stage uploads, read and delete their own files.
create policy "post_videos_insert_own" on storage.objects for insert to authenticated
with check (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "post_videos_delete_own" on storage.objects for delete to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
-- Signed URL issuance uses Storage SELECT and must be limited to legitimate viewers.
-- This relies on posts SELECT RLS, plus block relationships. Verify both before use.
-- BLOCKED: Do not grant viewer SELECT until a reviewed authorization mechanism
-- verifies posts visibility, bidirectional blocks, and the policy composition.
-- An overly broad Storage SELECT would permit arbitrary signed URLs.
-- Only the owner may SELECT during the current staging phase.
create policy "post_videos_read_own" on storage.objects for select to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
-- IMPORTANT: SELECT policies for storage.objects are OR-composed with other policies.
-- Review ALL existing Storage policies for broader read grants.
-- No server-side duration enforcement is provided here; activation is BLOCKED.
);
alter table public.posts add constraint posts_video_or_images_exclusive
  check (video_path is null or coalesce(cardinality(image_urls), 0) = 0);
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('post-videos', 'post-videos', false, 20971520, array['video/mp4','video/webm'])
on conflict (id) do nothing;
-- Owners can stage uploads, read and delete their own files.
create policy "post_videos_insert_own" on storage.objects for insert to authenticated
with check (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
create policy "post_videos_delete_own" on storage.objects for delete to authenticated
using (bucket_id = 'post-videos' and (storage.foldername(name))[1] = (select auth.uid())::text);
-- Signed URL issuance uses Storage SELECT and must be limited to legitimate viewers.
-- This relies on posts SELECT RLS, plus block relationships. Verify both before use.
create policy "post_videos_read_post_viewers" on storage.objects for select to authenticated
using (bucket_id = 'post-videos' and (
  (storage.foldername(name))[1] = (select auth.uid())::text
  or exists (
    select 1 from public.posts p where p.video_path = name
    and not exists (
      select 1 from public.user_blocks b
      where (b.blocker_id = (select auth.uid()) and b.blocked_id = p.user_id)
         or (b.blocked_id = (select auth.uid()) and b.blocker_id = p.user_id)
    )
  )
));
-- IMPORTANT: SELECT policies for storage.objects are OR-composed with other policies.
-- Review ALL existing Storage policies for broader read grants.
-- No server-side duration enforcement is provided here; activation is BLOCKED.

-- Video duration is metadata-dependent: bucket MIME/size limits do NOT enforce 30 seconds.
-- Keep UI publication disabled until a trusted upload validation pipeline is in place.

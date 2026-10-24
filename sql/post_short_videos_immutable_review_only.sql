-- REVIEW ONLY: production-oriented immutable Storage policy candidate.
-- DO NOT APPLY to production. Isolated QA uses
-- sql/post_short_videos_candidate.sql with an owner DELETE test fixture.
-- Requires schema/security review, authenticated E2E and release approval.
--
-- Assumes bucket post-videos already exists and is private. No client
-- UPDATE or DELETE policies are created. Existing permissive policies
-- must be audited and revoked before this can be considered safe.
create policy "post_videos_immutable_insert_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and name ~ ('^' || (select auth.uid())::text ||
                '/[0-9a-f-]{36}[.](mp4|webm)$')
  );
create policy "post_videos_immutable_read_own" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
-- Deliberately no UPDATE or DELETE policies.
-- Upload client MUST use x-upsert:false. Storage rejects collisions.
-- Do not permit other permissive UPDATE/DELETE policies on this bucket.
-- No orphan cleanup without proven atomic conditional delete.

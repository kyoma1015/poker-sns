-- REVIEW ONLY: production-oriented immutable Storage policy candidate.
-- DO NOT APPLY to production. Isolated QA uses
-- sql/post_short_videos_candidate.sql with an owner DELETE test fixture.
-- Requires schema/security review, authenticated E2E and release approval.
--
-- Production read-only audit (2026-10-24): post-videos bucket absent; existing
-- storage.objects policies are scoped to avatars, comment-images, post-images,
-- and poker-id-card-og. This is a point-in-time observation, NOT approval.
-- Re-run a full policy/role/bucket audit before any future release.
-- Assumes bucket post-videos already exists and is private. No client
-- UPDATE or DELETE policies are created. Existing permissive policies
-- must be audited and revoked before this can be considered safe.
-- The append-only ledger and owner predicate must be installed first.
-- Replace the old unrestricted candidate INSERT policy; never retain both.
create policy "post_videos_immutable_insert_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and name ~ ('^' || (select auth.uid())::text ||
                '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](mp4|webm)$')
    and public.video_reserved_key_is_owned(name, (select auth.uid()))
  );
create policy "post_videos_immutable_read_own" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
  );
-- Published objects may be read by a caller who can SELECT the linked post.
-- The invoker's existing public.posts RLS decides visibility. Staged uploads
-- have no post and are NOT exposed to other users. Do not use SECURITY DEFINER.
-- This is a release candidate; audit all overlapping Storage SELECT policies.
create policy "post_videos_read_visible_post" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'post-videos'
    and exists (
      select 1 from public.posts p
      where p.video_path = storage.objects.name
        and p.user_id::text = (storage.foldername(storage.objects.name))[1]
    )
  );
-- Deliberately no UPDATE or DELETE policies.
-- Upload client MUST use x-upsert:false. Storage rejects collisions.
-- Do not permit other permissive UPDATE/DELETE policies on this bucket.
-- No orphan cleanup without proven atomic conditional delete.
-- REVIEW GATE: forbid permissive UPDATE/DELETE policies on post-videos;
-- storage.objects RLS policies are OR-combined, so this policy alone cannot
-- prove immutability if any other permissive policy allows mutation.
-- An alternate design can prohibit all updates/deletes for the entire object
-- lifetime and enforce insert-once UUID paths. That requires auditing every
-- permissive policy, privileged role, API upsert path, and worker. A path/hash
-- alone is not an immutability proof until those invariants are demonstrated.
-- Audit query: sql/video_storage_policy_audit_read_only.sql

-- Future release: require a durable reservation before ANY new Storage INSERT.
-- The ledger is append-only and reservation RPC execution is authenticated-owner scoped. This SQL is
-- review-only; isolated tests apply the ledger separately before uploads.
-- A permissive INSERT policy can bypass this predicate, so the full writer
-- inventory and policy audit remain mandatory release blockers.
-- The isolated QA INSERT policy must be replaced with this fenced policy
-- during a production migration; never OR-combine both.
-- Intended predicate (NOT executable until helper and grants are audited):
--   bucket_id = 'post-videos'
--   AND (storage.foldername(name))[1] = auth.uid()::text
--   AND public.video_reserved_key_is_owned(name, auth.uid())
-- The helper must be security-definer, read-only and strictly owner-scoped.
-- The helper is defined in video_permanent_key_reservation_review_only.sql.
-- This policy is NOT deployable until all permissive writers are audited.
-- Keep release gate OFF until that helper and writer inventory are complete.

-- ABA replacement remains a release blocker until every policy and privileged
-- path is proven unable to replace an existing object generation.

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
create policy "post_videos_immutable_insert_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and name ~ ('^' || (select auth.uid())::text ||
                '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](mp4|webm)$')
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
-- REVIEW GATE: forbid permissive UPDATE/DELETE policies on post-videos;
-- storage.objects RLS policies are OR-combined, so this policy alone cannot
-- prove immutability if any other permissive policy allows mutation.
-- An alternate design can prohibit all updates/deletes for the entire object
-- lifetime and enforce insert-once UUID paths. That requires auditing every
-- permissive policy, privileged role, API upsert path, and worker. A path/hash
-- alone is not an immutability proof until those invariants are demonstrated.
-- Audit query: sql/video_storage_policy_audit_read_only.sql

-- Future release: require a durable reservation before ANY new Storage INSERT.
-- The ledger is append-only and the RPC is service_role-only. This SQL is
-- review-only; isolated tests apply the ledger separately before uploads.
-- A permissive INSERT policy can bypass this predicate, so the full writer
-- inventory and policy audit remain mandatory release blockers.
-- The isolated QA INSERT policy must be replaced with this fenced policy
-- during a production migration; never OR-combine both.
create policy "post_videos_reserved_insert_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'post-videos'
    and (storage.foldername(name))[1] = (select auth.uid())::text
    and exists (
      select 1 from public.video_reserved_object_keys reserved
      where reserved.bucket_id = 'post-videos'
        and reserved.object_path = storage.objects.name
        and reserved.owner_id = (select auth.uid())
    )
  );
-- IMPORTANT: authenticated has no SELECT privilege on the private ledger.
-- Therefore this illustrative policy is NOT deployable as written: the
-- existence check needs a security-definer boolean helper with an explicit
-- authenticated EXECUTE grant, plus a fully audited Storage policy replacement.
-- Keep release gate OFF until that helper and writer inventory are complete.

-- ABA replacement remains a release blocker until every policy and privileged
-- path is proven unable to replace an existing object generation.

# Video MVP production rollout and rollback — staged, NOT approved

## Candidate artifacts

- `tests/video/production_additive_candidate.sql`: **not yet executed or tested against a production-equivalent clone**. It is an additive SQL candidate, not a migration approved for production. Must audit idempotency, Storage policy inheritance, grants, RPC execution roles and existing posts constraints.
- `api/video-production-supabase-adapters.ts`: requires exact Supabase HTTPS origin, per-request owner JWT and `VIDEO_PRODUCTION_FENCED_READY=true`. It deliberately throws in `assertServerAttestationAvailable()` regardless of the flag until independent attestation is release-approved; no service-role key is used by this adapter.
- `api/video-finalize.ts`: defaults to HTTP 503; enables production adapter only behind the same server gate. QA injected adapter remains restricted to 127.0.0.1:56321.
- `api/video-media.ts`: uses existing posts SELECT RLS instead of nonexistent posts.is_public. This matches existing authenticated-post visibility; no separate private-post semantics may be assumed.
- `src/videoApi.ts`: `VIDEO_SERVER_ENABLED` defaults to false unless `VITE_VIDEO_SERVER_ENABLED=true` is explicitly built. **Do not flip before production backend and rollback are verified**.

## Blocking verification

1. Apply SQL candidate to a disposable clone of **real** production schema, never the live project first. Verify pre/post schema and no existing rows modified.
2. Prove private bucket INSERT-only (no client UPDATE/DELETE/upsert), authenticated owner access, generation-fenced RPC, replay/idempotency, unauthorized owner, wrong generation, hash mismatch and parallel publish. Audit other broad Storage policies and service-level mutation paths.
3. Check `storage.objects.owner_id` and Storage API behavior on actual Supabase version; inspect existing grants and whether the authenticated JWT can execute only the reviewed SECURITY DEFINER RPCs. The attested publication RPC verifies `auth.uid()`, the server HMAC, nonce, reservation and Storage generation; privileged roles can bypass RLS and must be audited separately.
4. Confirm Vercel ffprobe binary works in serverless Node runtime and that HMAC secrets never reach browser; verify production server env, exact URL, and secret scopes without printing values.
5. Run staging E2E from actual Timeline including unauthorized media read, cross-user visibility, upload rejection, retries and rollback. Check whether Vercel media 20MB buffering fits function constraints.
6. Approve operational visibility model: existing posts SELECT RLS allows all authenticated users to see posts; both `api/video-media.ts` and the review-only `post-videos` Storage SELECT policy follow it. An isolated private/public toggle is test-only, not a production `posts.is_public` column.
7. Keep orphan cleanup disabled; no generation-proven safe deletion path has been released.

## Non-destructive rollback

- **First:** set `VIDEO_PRODUCTION_FENCED_READY` to anything except `true` in server environment and redeploy (server returns 503); build client with `VIDEO_SERVER_ENABLED=false` and redeploy. Confirm upload entry is hidden.
- Preserve `posts.video_*`, all existing video rows, Storage objects and published media during rollback. **Do not DROP columns, tables, functions, buckets, objects, or policies automatically.**
- Revert/promote previous tested Vercel deployment after checking compatibility. Existing non-video posts remain readable.
- After incident investigation, decide separately whether to retain or retire unused video RPC privileges; never perform automatic destructive cleanup.

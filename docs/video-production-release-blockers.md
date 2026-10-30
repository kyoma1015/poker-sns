# Poker ID video MVP — production release gate (2026-10-25)

Status: **NO-GO**. This is a release audit, **not** an executable migration.

## Verified on isolated stack

- HEAD `8e14a26d34b368a3cb755ca80726b23aabd1d77a`: Video SQL #40449633840, Storage HTTP #40449633889, Poll-only #40449633851 all SUCCESS. Storage HTTP logs confirm foreign JWT reads RLS-visible published videos while private and staging videos remain denied.

- HEAD 5b92280db9ca2fd6c1e4e3b20bf967264ddb2103: Video Storage HTTP #40116811080, Video SQL #40116811088, Poll-only #40116811078: all SUCCESS.
- Chromium log proves actual Timeline.tsx file selection -> real isolated Storage HTTP upload -> real finalize HTTP -> RLS PostgREST feed -> playback.
- The isolated browser Vite transform sets VIDEO_SERVER_ENABLED=true in memory only. Production `src/videoApi.ts` remains disabled unless explicitly built with `VITE_VIDEO_SERVER_ENABLED=true`.

## Live Supabase read-only audit

Project: poker-id (ephptepeuespnxtzdqby). Existing public.posts columns: id, created_at, user_id, content, post_type, result_type, result_id, image_urls, style_snapshot, quote_post_id.

- Missing: video_path, video_generation, video_sha256, video_duration_seconds.
- Missing Storage bucket: post-videos.
- Missing public.video_* RPC functions.
- Existing posts SELECT policy `Authenticated users can view posts` uses `true`, unlike the isolated owner/private test. **Never copy isolated RLS semantics to production without a product visibility decision and migration audit.**

## Required before deployment

1. Design and review **additive, idempotent, non-destructive** migration for real public.posts and private post-videos bucket, with insert-once owner-scoped Storage permissions, published-viewer SELECT tied to existing posts RLS, explicit grants and server-HMAC-attested owner-JWT RPC. Prove that no UPDATE, DELETE, upsert, or alternate privileged replacement path can invalidate storage.objects.id as an immutable generation fence.
2. Audit real production posts SELECT RLS and media authorization. Current `api/video-media.ts` uses existing posts SELECT RLS and does **not** reference the nonexistent `posts.is_public` column. The isolated public/private toggle is QA-only. Confirm the production authenticated-public visibility decision and every overlapping Storage SELECT policy before release.
3. The production adapter contains per-request owner JWT, immutable generation checks, bounded ffprobe integration and HMAC-attested RPC candidate, but `assertServerAttestationAvailable()` deliberately throws unconditionally. Do not remove this hard stop until independently provisioned DB HMAC keys, production-equivalent clone QA, privilege audit and release approval are proven.
4. Validate runtime environment variables without exposing secrets, confirm Vercel Node runtime/ffprobe availability, and run production-equivalent staging E2E including unauthorized access, upload rejection, duplicate publish, storage overwrite/delete denial and regression.
5. Implement controlled feature enablement **only after** all checks; do not flip VIDEO_SERVER_ENABLED to true until API, DB, and Storage are proven. Keep unproven orphan deletion fail-closed.
6. Prepare database rollback that preserves already published media, a feature-gate rollback, monitoring, and a tested staging promotion. No main merge or production deployment before this gate is green.

## Evidence rule

Isolated QA success proves the isolated fixture, **not** production readiness. No destructive SQL, production writes, main merge, or production deployment are authorized by this document.


## Runtime executable and feature-gate release blockers (2026-10-25)

- `api/video-ffprobe.ts` accepts only an absolute `FFPROBE_BINARY_PATH` when configured; otherwise uses `ffprobe` on PATH. This is **not** evidence that Vercel bundles a working executable. A trusted, version-pinned Linux ffprobe binary must be packaged with the serverless function and executed on a Vercel preview before enabling production.
- `src/videoApi.ts` now uses the explicit build-time `VITE_VIDEO_SERVER_ENABLED=true` opt-in. It remains disabled when the environment variable is absent. Set it only after backend, storage, JWT/RLS and media QA pass.
- `VIDEO_PRODUCTION_FENCED_READY=true` is a separate server-only runtime gate. Never set it based only on SQL or isolated CI results.
- Production rollout is **NO-GO** until the bundled ffprobe executable, serverless invocation, protected Storage API and real JWT access tests pass. A no-op/failed upload must not delete staged objects.

## Verified live Vercel preview and production release prerequisites (2026-10-27)

- Preview deployment `dpl_5UoZu4fBa2sJwjQNWSvkdEKFqkZj` is `READY` for exact commit `160a09a9949e4a162c4613913737641dc3737ce1`.
- Preview `GET /internal/video/runtime-attestation` returned HTTP 200 and `{"ffprobe":"executable"}`. This proves the packaged executable can run on this Vercel preview, **not** that publishing works end-to-end on production.
- Preview `GET /internal/video/finalize` returned HTTP 405, consistent with the method restriction. Authenticated media playback is **not yet proven** on the preview; an attempted media request was blocked by deployment authentication.
- Live Supabase read-only query: 26 existing `public.posts`, 7 `storage.objects`; `post-videos` bucket count 0; `video_publish_attested_v1` RPC count 0. No live migration was applied.
- Vercel production environment inventory (names only; values not decrypted) contains `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`. It does **not** contain `VIDEO_ATTESTATION_KEY_HEX`, `VIDEO_ATTESTATION_KEY_ID`, `VIDEO_ATTESTED_RPC_RELEASE_APPROVED`, or `VIDEO_PRODUCTION_FENCED_READY`.
- Backup readiness remains **NO-GO**: existing `scripts/poll_private_export.sh` produces a private roles/schema/data SQL export only, not Storage object bytes; neither a real production export nor an isolated restore has been completed. The connected Supabase tool has no complete DB dump/Storage bytes export facility. Never treat a read-only SQL query, metadata inventory, or synthetic restore as a recoverable production backup.
- Release order: (1) obtain encrypted/private DB and Storage-byte exports using trusted authorized credentials and a non-repository destination; (2) restore and verify both in isolation; (3) review/apply additive production migration and least-privilege HMAC/RPC/Storage policies; (4) provision distinct server-side HMAC keys without disclosing values; (5) perform production-equivalent authenticated and unauthorized E2E; (6) explicitly approve release flags, merge, deploy, and test; (7) keep rollback gates ready. No production write, merge, or feature enablement while these prerequisites are unmet.

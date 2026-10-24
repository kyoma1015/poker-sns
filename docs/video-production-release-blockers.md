# Poker ID video MVP — production release gate (2026-10-25)

Status: **NO-GO**. This is a release audit, **not** an executable migration.

## Verified on isolated stack

- HEAD 5b92280db9ca2fd6c1e4e3b20bf967264ddb2103: Video Storage HTTP #40116811080, Video SQL #40116811088, Poll-only #40116811078: all SUCCESS.
- Chromium log proves actual Timeline.tsx file selection -> real isolated Storage HTTP upload -> real finalize HTTP -> RLS PostgREST feed -> playback.
- The isolated browser Vite transform sets VIDEO_SERVER_ENABLED=true in memory only. Production src/videoApi.ts remains false.

## Live Supabase read-only audit

Project: poker-id (ephptepeuespnxtzdqby). Existing public.posts columns: id, created_at, user_id, content, post_type, result_type, result_id, image_urls, style_snapshot, quote_post_id.

- Missing: video_path, video_generation, video_sha256, video_duration_seconds.
- Missing Storage bucket: post-videos.
- Missing public.video_* RPC functions.
- Existing posts SELECT policy `Authenticated users can view posts` uses `true`, unlike the isolated owner/private test. **Never copy isolated RLS semantics to production without a product visibility decision and migration audit.**

## Required before deployment

1. Design and review **additive, idempotent, non-destructive** migration for real public.posts and private post-videos bucket, with insert-once owner-scoped Storage permissions, explicit grants and service-only fenced RPC. Prove that no UPDATE, DELETE, upsert, or alternate privileged replacement path can invalidate storage.objects.id as an immutable generation fence.
2. Audit real production posts SELECT RLS and media authorization. Current api/video-media.ts reads `posts.is_public`, which does **not** exist in production. Define owner/public/follower visibility explicitly; do not silently expose private videos.
3. Implement production finalize adapters; currently api/video-finalize.ts intentionally returns 503 for all non-isolated requests. Ensure per-request JWT validation, immutable triple snapshot, bounded ffprobe, fenced transactional publish, idempotent reconcile, and safe unknown-outcome recovery.
4. Validate runtime environment variables without exposing secrets, confirm Vercel Node runtime/ffprobe availability, and run production-equivalent staging E2E including unauthorized access, upload rejection, duplicate publish, storage overwrite/delete denial and regression.
5. Implement controlled feature enablement **only after** all checks; do not flip VIDEO_SERVER_ENABLED to true until API, DB, and Storage are proven. Keep unproven orphan deletion fail-closed.
6. Prepare database rollback that preserves already published media, a feature-gate rollback, monitoring, and a tested staging promotion. No main merge or production deployment before this gate is green.

## Evidence rule

Isolated QA success proves the isolated fixture, **not** production readiness. No destructive SQL, production writes, main merge, or production deployment are authorized by this document.

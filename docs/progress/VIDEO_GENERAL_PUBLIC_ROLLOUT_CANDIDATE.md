# Video MVP general-public rollout candidate (2026-10-30)

Status: **DRAFT / NOT APPLIED**. This is a code candidate on PR #131 only.
Existing production: testplayer-only, tested separately. Never activate public mode by clearing the existing UUID allowlist.

## What changed

- `server/video-production-rollout.mjs` permits an authenticated non-allowlisted user only when **both** `VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED=true` and `VIDEO_PUBLIC_ROLLOUT_ENABLED=true` are set server-side. Otherwise the existing `VIDEO_ALLOWED_USER_IDS` requirement remains.
- Even with both flags on, the request-scoped JWT must pass the `video_rollout_member` or `video_rollout_allowed` RPC. No bypass of database authorization.
- `sql/video_general_public_rollout_candidate.sql` creates an independent **default-OFF** `video_private.general_public_rollout` switch and updates `video_rollout_member()` to accept the existing per-user allowlist **or** that switch. The JWT must be valid and unexpired, with `auth.uid()`.
- Existing `video_private.rollout_settings.enabled` remains the global stop for new reservations and publication. Existing video ownership, signed finalize, private Storage, non-destructive hide, MIME, duration and byte restrictions remain unchanged.
- No new public access for anonymous viewers: anonymous Storage/post visibility remains restricted as in the limited rollout.

## Safe sequence (explicit approval required for every production mutation)

1. Confirm PR #131 exact SHA; validate changed SQL in a throwaway Auth/PostgREST/Storage environment and server-gate tests. Verify iPhone Safari MOV output separately: Chromium CI is not iPhone evidence.
2. Capture the existing production policies, posted video count, and deployment identity read-only. Explicitly accept that no full production disaster-recovery restore has been proven.
3. Apply **only** `sql/video_general_public_rollout_candidate.sql` to the existing production project after approval. Default `general_public_rollout.enabled=false`. Verify existing testplayer posting still works and non-allowlisted users remain denied. Do not reapply the first-install migration.
4. Review and deploy PR #131 with video general-public flags still **OFF**, retaining `VIDEO_ALLOWED_USER_IDS` with testplayer only.
5. After iPhone and negative-authorization HTTP validation and a separate, explicit general-release approval, enable `video_private.general_public_rollout.enabled=true` and both new server-side flags. Ensure existing `video_private.rollout_settings.enabled` is true only for the approved rollout. Recheck one other authenticated test account, invalid JWT, Storage owner denial, and emergency stop.
6. If anything fails, set `video_private.rollout_settings.enabled=false` **first**, then `video_private.general_public_rollout.enabled=false`, then `VIDEO_PUBLIC_ROLLOUT_ENABLED=false`; keep `VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED` off during rollback. Preserve rows, stored files, previous user allowlist and policies. No destructive schema rollback.

No privileged API credentials in browser `VITE_*` variables. No full-backup claim, additional charges, main merge, SQL application or production deployment within this candidate work.


## Exact iPhone Safari acceptance (requires human device, no production mutation until approval)

1. On iPhone Safari, visit **the protected exact-SHA Preview**, not the production site. Sign in with the authorized test account through the normal app UI. If Preview is protected by Vercel Authentication, obtain access through the authorized Vercel flow; do not disable or bypass Deployment Protection. Keep test credentials and tokens out of chat, screenshots and CI logs.
2. In the iPhone Camera, capture a **2–5 second** MOV with audible speech and visible motion, under 20 MiB. Keep the app foregrounded for conversion. Use the Timeline's regular composer > Attach > Video and select this MOV.
3. Confirm in-place conversion to a `-converted.mp4` preview, correct aspect ratio, actual moving frames and audible recorded sound, with no remote upload before the user submits. Check that video duration is correct; mute/empty audio or frozen frames is a failure.
4. Repeat with an available HEVC/HDR iPhone capture. If Safari cannot decode or MediaRecorder cannot encode H.264 MP4, check the explicit failure message and **no reservation, Storage upload or post**; do not call that codec supported.
5. Cancel one conversion by closing the composer or switching account, then verify no stale thumbnail/attachment appears after reopening. Keep the app visible during valid recording.
6. A source MOV over 20 MiB is *currently rejected before conversion*. A clip longer than 30 s is rejected. This is a product limitation, not proof of all iPhone Camera defaults working. The documented fallback is the native iPhone Shortcuts **Encode Media** route producing an H.264 MP4, then attach the resulting file.
7. On Preview, verify posting/replay only if it is independently connected to an authorized isolated test backend. Do **not** point an unreviewed Preview at production writes. The ordinary production testplayer-only site **does not include this PR** until approved and deployed.

## Non-allowlisted authenticated JWT negative HTTP verification

This is a read/negative-access check, not a way to create or modify someone else's content. Use a **consenting, existing, authorized test account** other than testplayer (previously used `@kyoma` only if explicitly authorized). Log in to the current **production** origin through the ordinary UI. Do not create user accounts or modify RLS/allowlists for the test.

- Obtain the account's JWT solely within its authorized live browser session or a secure local test runner. Do **not** paste it in chat, CLI arguments, GitHub Actions, browser URL query params or logs. Do not copy testplayer's bearer token into the other account's session.
- Make exactly one ordinary authenticated `GET /internal/video/media/<verified-visible-video-post-uuid>` on the *same production origin*, with `Authorization: Bearer <that account JWT>` and `cache: no-store`. Use the existing real video post ID from an authorized read-only admin lookup (not a guessed path). The existing test video is hidden, so **404 alone cannot prove a nonmember's access is denied**; separately assert the test JWT gets `video_rollout_member=false` and that a request with the same nonmember token to the existing media endpoint does **not** return any bytes. If an existing non-hidden video is unavailable, record the media comparison as **BLOCKED**, not PASS.
- Expected before general-public activation: nonmember `video_rollout_member=false`; media request not 200, `Content-Type` not video, **zero playable media bytes**, and no writes or change to nonce, reservation, post or object counts. The current API's exception handler may answer **503** on authz denial; do not misinterpret that HTTP status as an authorization PASS by itself. Invalid or expired JWT must be refused separately in isolated tests (already covered).
- The prior @kyoma UI-level upload rejection establishes only that the operation failed; it does **not** establish the media API denied the right request. Do not label it a complete negative HTTP PASS.
- When the public rollout is finally authorized, repeat this test in a controlled staged window: the same authenticated nonmember should become allowed only after **both** server flags and the new private DB public membership switch are enabled, while anonymous/invalid JWT stays denied. Do not switch production flags just to run a preapproval test.

## Frozen release manifest (not an authorization)

- GitHub Draft PR #131 branch `codex/video-mov-native-conversion-20261030`. Reconfirm final HEAD and diff before requesting approval; HEAD changes after this document invalidate prior SHA assumptions.
- Based on current production merge `0e85cb2981b6290247eded54b695ad43d2e00338`, deployment `dpl_2Vu7D9giK8x73LyrfAdrzq6J5RMV`.
- New SQL **only**: `sql/video_general_public_rollout_candidate.sql`. The first-install `sql/video_production_limited_rollout.sql` is **already installed**; do not rerun it. Review the `CREATE OR REPLACE FUNCTION public.video_rollout_member()` effect on current RLS and grants.
- Existing server-only flags: `VIDEO_PRODUCTION_LIMITED_ROLLOUT=true`, `VIDEO_PRODUCTION_FENCED_READY=true`, `VIDEO_ATTESTED_RPC_RELEASE_APPROVED=true`, `VIDEO_SERVER_ENABLED=true` (when deliberately enabled), `VIDEO_ALLOWED_USER_IDS=<unchanged existing testplayer UUID>`. Preserve existing signing key ID/secret **without reading, rotating or reprinting it**. Keep `FFPROBE_BINARY_PATH` and existing production Supabase URL and anon key unchanged.
- **New server-only flags**: `VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED=false` and `VIDEO_PUBLIC_ROLLOUT_ENABLED=false` until the separate general-public activation approval. Both must be the literal string `true` for general-public server acceptance; never use `VITE_` names for these.
- Existing client flag `VITE_VIDEO_SERVER_ENABLED=true` only on the deliberately reviewed candidate production build. Setting it is UI availability, *not* an authorization decision.
- DB default `video_private.general_public_rollout.enabled=false`. Existing `video_private.rollout_settings.enabled` remains the independent global mutation stop. There is no migration that makes guests anonymous video viewers.
- Rollback order: first stop the global DB switch `video_private.rollout_settings.enabled=false`; then `video_private.general_public_rollout.enabled=false`; then disable `VIDEO_PUBLIC_ROLLOUT_ENABLED` and `VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED` on Vercel and redeploy reviewed flags; if the application itself regresses, build/deploy a known-safe previous SHA normally (a one-click rollback might be plan-gated). Never DROP, DELETE, overwrite Storage, or remove other users' posts. Database restoration is **not** guaranteed without a verified full backup.

**Release approval must authorize only this exact final HEAD, the above new migration, reviewed Vercel env changes, the controlled main merge + production deployment, and separately the public ON flip after iPhone + negative JWT acceptance. No general public enablement may occur on a CI result alone.**

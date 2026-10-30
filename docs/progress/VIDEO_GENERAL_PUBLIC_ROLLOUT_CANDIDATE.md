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

# Short-video candidate — implementation stage 2 (not enabled)
- Video selection, client validation and local preview: Timeline.
- Video playback: Timeline and PostDetail use short-lived signed URLs when video_path exists.
- Upload and deletion helpers exist, but upload is deliberately NOT connected to post creation.
- Post deletion attempts to remove its video from private Storage after successful DB deletion.
- SQL remains review-only and is NOT production-ready.
- Blocking issues: server-side duration validation, authorized viewer SELECT RLS and its interactions with existing policies, verified post-video lifecycle/cleanup, database acceptance tests.
- No production changes, no main merge.

## Review finding (round 6)
- Removed premature broad viewer SELECT policy from candidate SQL. Owner-only SELECT is staged; viewer authorization remains BLOCKED.
- Corrected the video_path SQL regex to use [.] instead of ambiguous backslash escaping.
- Added strict owner-path validation for cleanup.
- Added static regression checks for disabled publication, private bucket, and restricted SELECT.
- GitHub's general isolated PostgREST QA does not prove this un-applied candidate SQL works; do not report video end-to-end QA as passed.

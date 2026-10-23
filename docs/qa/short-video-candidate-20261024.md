# Short-video candidate — implementation stage 2 (not enabled)
- Video selection, client validation and local preview: Timeline.
- Video playback: Timeline and PostDetail use short-lived signed URLs when video_path exists.
- Upload and deletion helpers exist, but upload is deliberately NOT connected to post creation.
- Post deletion attempts to remove its video from private Storage after successful DB deletion.
- SQL remains review-only and is NOT production-ready.
- Blocking issues: server-side duration validation, authorized viewer SELECT RLS and its interactions with existing policies, verified post-video lifecycle/cleanup, database acceptance tests.
- No production changes, no main merge.

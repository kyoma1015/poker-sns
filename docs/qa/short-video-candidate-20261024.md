# Short-video candidate (isolated; not integrated)
- 30 seconds, 20 MiB, MP4/WebM: client validation helper.
- Private Storage bucket and RLS: review-only SQL candidate.
- No changes to Timeline or PostDetail yet; upload/playback/delete are NOT implemented.
- Security blockers: signed URL access design, backend duration validation, storage cleanup on post failure, existing posts schema verification, and policies for legitimate viewers.
- No production DB, Storage, deployment, or main changes.

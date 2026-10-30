# Isolated Supabase Storage API E2E — implementation plan (NOT RUN)
This is a separate test from `tests/video/run_isolated.sh`. The PostgreSQL fixture is **not** the Supabase Storage HTTP API.
Use an ephemeral local Supabase stack with real Auth, Postgres and Storage (e.g. a pinned Supabase CLI stack) and disposable owner/viewer accounts.
Apply `sql/post_short_videos_candidate.sql` only to that isolated instance, after reconciling official storage schema and policy collisions.
Assertions must use authenticated `supabase-js` requests, never service-role requests:
1. Owner uploads a 2s valid MP4 at `<owner-uuid>/<file-uuid>.mp4`; viewer attempts same owner path and must fail.
2. Viewer cannot list/download/create signed URL/delete the owner's private object.
3. Owner creates 300s signed URL and retrieves exact bytes; a viewer without the URL must not retrieve it. Note: anyone possessing a signed URL can use it until expiry; do not interpret signed URLs as per-request viewer authorization.
4. Reject 20MiB+1 bytes and incorrect MIME. Verify the object is absent after rejection.
5. Delete owner object, verify GET fails and object is absent.
6. Simulate failed post finalization and verify staged object is reclaimed. This is NOT implemented in the app.
7. A 31s video below 20MiB must be rejected by trusted-server finalization, not by browser metadata alone. This is NOT implemented in the app.
**Current blockers:** No isolated Storage HTTP stack or Auth fixtures; no trusted finalization API; no safe non-owner viewer access model; no server-side upload cleanup.
Never point this QA at the production Supabase project or credentials. Never relax owner-only RLS to make the tests pass.

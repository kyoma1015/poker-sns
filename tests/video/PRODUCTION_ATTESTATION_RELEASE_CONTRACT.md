# Video publish: server attestation release contract (NO-GO)

This is a release-blocking implementation contract, not an approval to enable VIDEO_SERVER_ENABLED.

## Current bypass and boundary
The browser can invoke authenticated PostgREST RPCs directly. Consequently the browser-provided SHA-256 and duration are **not evidence** of server ffprobe inspection. A SECURITY DEFINER function checking auth.uid() and Storage generation does not fix this. The current `video_production_publish_fenced` RPC MUST remain unexecutable by authenticated, anon and service_role while it accepts unsigned metadata.

## Required implementation
1. Provision an independent 256-bit attestation key in a DB-private secret store and the video finalizer runtime. Never embed the key in SQL migrations, VITE_ variables, source, frontend bundles, or the browser. Do not reuse Supabase JWT signing keys, anon keys or service_role.
2. After owner JWT verification, bounded private Storage read, immutable generation check, ffprobe inspection, SHA-256 computation, and second JWT/generation verification, the server creates an HMAC-SHA256 proof over a canonical, versioned, length-delimited payload containing owner UUID, exact Storage path, immutable Storage object UUID, media SHA-256, measured duration in canonical units, post content digest, expiration and a random single-use nonce. Include a key identifier for rotation. Do not trust client-supplied claims.
3. A SECURITY DEFINER database RPC with a fixed empty search_path verifies the HMAC in constant time using only a DB-private secret. The secret must not be accessible to authenticated, anon, service_role, or via exposed PostgREST views/functions. The RPC checks auth.uid() = owner, expiration, nonce uniqueness, exact Storage generation under row lock, and matching reservation. Atomically consume nonce and insert or reconcile the uniquely fenced post. Reject replay with different content, path, generation or media fingerprint.
4. Define an explicit key provisioning and rotation procedure that fails closed on missing/mismatched secrets. Do not make the finalizer callable until isolated production-equivalent SQL and real HTTP E2E exercise the exact new RPC and runtime adapter. Never introduce a service_role Storage mutation bypass.
5. On ambiguous commit, reconcile using exact owner/path/generation/fingerprint; never delete Storage. Orphan recovery must be bounded and owner scoped. Playback must use the viewer's JWT and SELECT RLS; cross-owner requests must fail.

## Release-blocking tests
- Owner JWT calls publish directly with invented ffprobe fields and missing/invalid HMAC: denied, no post.
- Other JWT and anon with valid-looking attestation: denied, no post.
- Valid attestation, exact generation, owner and nonce: one post; same request idempotent; altered content rejected.
- Expired proof, replayed nonce, wrong key, tampered SHA-256, duration, content, owner or Storage generation: denied.
- Revoked JWT during ffprobe, replaced object generation, >20 MiB, >30 seconds, wrong MIME and invalid container: no post.
- Storage private read own succeeds, foreign read fails, authenticated overwrite/delete fails.
- Real HTTP reservation → upload → ffprobe → attested publish → viewer playback and ambiguous-commit recovery on disposable stack.
- Both release toggles remain disabled in production until a separately authorized release.

**Status:** NO-GO. Existing isolated QA tests use a different privileged publication adapter and cannot prove the production attestation path. A green CI is not release evidence until these cases are implemented against the same code.

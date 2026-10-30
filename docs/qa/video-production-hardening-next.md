# Video MVP — production hardening continuation (review only)

Status: NO-GO. This document does not authorize any production writes or deployment.

## Current evidence
- Draft PR #123, baseline 79ea9f0d87c249be4014709500c93ed475ae514d.
- Isolated SQL, Storage HTTP, Poll-only workflows passed at baseline.
- Production adapter unconditionally throws in assertServerAttestationAvailable(); reserve HTTP is intentionally isolated-only.
- Isolated attested HTTP E2E already checks anonymous denial, owner JWT, wrong key ID, HMAC mismatch, nonce replay, private media playback, and orphan non-deletion. Do not claim these prove production readiness.

## Required implementation order
1. Define an independent key provisioning and rotation runbook: generate keys outside source control, provision same key ID/secret independently to trusted server and private DB table, activate new ID, test signatures, retire old ID only after in-flight TTL and rollback window. Do not expose private schema or log key material.
2. Verify actual production schema/policies **read-only**; reconcile public.posts visibility and media authorization rather than copying isolated RLS. Preserve existing posts.
3. Replace unconditional attestation gate only when independent provisioning, authenticated RPC permissions, replay prevention, storage generation fencing, and staging JWT HTTP E2E have passing evidence. Never remove the gate merely because a feature flag is true.
4. Complete reservation on a narrowly authorized owner-JWT path with bounded abuse controls and fail-closed responses. Avoid service-role API bypass.
5. Exercise real upload → finalize → private feed → media GET → browser playback; test unauthorized access, owner revocation, malformed video, double publication, storage overwrite/delete denial, orphan quarantine.
6. Verify existing Vercel preview SHA and ffprobe attestation via actual HTTP 200; READY alone is insufficient.
7. Re-run all three CI suites on resulting SHA and record links, results, and limitations. Keep VIDEO_SERVER_ENABLED=false and production flags OFF.

## Release decision
NO-GO until reviewed production migration, secret provisioning, preview runtime proof, and staging authorization evidence exist. No main merge, production DB/Storage writes, production deploy, or extra billing.

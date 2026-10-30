# Poker ID video MVP — release gate (2026-10-26)

Status: **ISOLATED QA PASS / PRODUCTION NO-GO**. This document is an evidence inventory, not deployment approval.

## Verified
- Branch `feature/sns-short-video-candidate-20261024`, Draft PR #123.
- Commit `56c056630e329411dab49327e477c07732e5921f` passed SQL isolated QA `40205662870`, Poll-only isolated QA `40205662914`, and Storage HTTP isolated QA `40205662990`.
- Isolated browser tests cover upload, finalize, playback and 15-second metadata timeout.
- Isolated Storage tests cover reserved owner writes, unreserved/foreign rejection, key non-reuse, unauthorized RPC denial, and immutable upload.
- Pinned ffprobe bundle executes in Linux CI. This does **not** prove execution in a Vercel serverless deployment.
- Orphan cleanup remains non-destructive: version mismatch, missing pin, and unproven atomic deletion are quarantined/retried. **No Storage delete**.

## Production blockers (must not silently bypass)
1. Production Supabase `post-videos` bucket and reserved-key schema/policies have not been applied. Read-only inventory found no `post-videos` bucket. Existing authenticated Storage policies target other buckets. `postgres`, `service_role`, and `supabase_admin` can bypass RLS; enumerate and review every privileged video-writing path before release.
2. Preview deployment READY is not runtime proof. The existing preview-only `/internal/video/runtime-attestation` handler must be invoked on an already-authorized deployment to demonstrate that bundled ffprobe is executable; inspect the exact deployed SHA and 200 response. Do not trigger new deployments or extra billing without approval.
3. No verified atomic conditional delete by object version. Keep orphan deletion disabled; use non-destructive quarantine/retry and monitor retention/cost until a formally reviewed implementation exists.

## Release requirements
- Explicit owner approval for production Supabase changes, including bucket creation, migration, grants, Storage policies, and privileged-writer audit; apply as a separately reviewed, reversible batch.
- Successful Vercel runtime attestation on the exact release SHA, plus environment/feature flag and API authentication checks.
- Re-run the three isolated CI suites on release SHA and complete production smoke testing only after explicit authorization.
- Keep `VIDEO_PRODUCTION_FENCED_READY` and `VITE_VIDEO_SERVER_ENABLED` **OFF** until all requirements are met. Do not merge, publish, deploy, or delete Storage objects automatically.

**Release decision: NO-GO.** Isolated MVP implementation is validated; production authorization and evidence are pending.

# Video recovery: production release runbook (review only)

Status: **NOT APPROVED / NOT DEPLOYED**. Draft PR #132. No production change is authorized by this document.

## Verified production baseline (read-only audit, 2026-10-31 JST)
- `public.video_reserve_object_key(uuid,text)` and `public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)` exist. `authenticated` EXECUTE yes; `anon` EXECUTE no.
- `public.video_rollout_member()`, `public.video_rollout_allowed()`, and `public.video_hide_own(uuid)` exist.
- `public.posts` and `public.video_reserved_object_keys` have RLS enabled.
- `storage.objects` contains multiple preexisting video policies; their effective OR-combined semantics **must be reviewed before any rollout**.
- `video_private.general_public_rollout` and `video_private.consumed_nonces` exist.
- `video_private.recovery_manifests` and `public.video_bind_recovery_manifest_v1`, `public.video_recovery_state_v1`, `public.video_publish_recovered_attested_v1` are **absent**.
- Current source: `src/videoRecoveryCandidate.ts` sets `VIDEO_RECOVERY_CANDIDATE_ENABLED=false`; `server/video-recovery-candidate.ts` allows production **status only** by independent opt-in; other mutations disabled. Do not turn this boolean on in isolation.
- `src/videoApi.ts` gates ordinary video APIs with `VITE_VIDEO_SERVER_ENABLED`; `server/video-production-rollout.mjs` checks server flags, user authorization and DB decisions. Cloud-test origin guards cannot be relaxed.

## Candidate migration (not executable against production without separate authorization)
The **isolated validation fixture** is `tests/video/recovery_candidate_review_only.sql`. It provides the manifest table and three RPCs and is covered by isolated HTTP CI. It is **not** a reviewed production migration, should not be blindly executed in Supabase SQL Editor, and must not be auto-run during deployment.

Before preparing a production-targeted SQL migration:
1. Snapshot current PostgreSQL definitions (including `pg_get_functiondef`, roles, grants, owners, search paths, RLS, storage policy USING/WITH CHECK, constraints and indexed columns) and compare **all** dependencies with the fixture. Avoid `DROP ... CASCADE`.
2. Review the isolated fixture against PostgreSQL/SQL Editor behaviour and build a transactional, idempotent migration with an explicit preflight assertion; preserve existing RPC definitions, roles, policies and historical rows. Avoid broad REVOKE on an existing schema. Ensure `SECURITY DEFINER` functions never transiently expose PUBLIC EXECUTE; default grant control must be transactional. Limit EXECUTE to authenticated only where appropriate.
3. Independently review `auth.sessions` lookups, session revocation, JWT expiration after lock waits, nonce consumption, storage-generation and reservation locks, `SHA256`, `ffprobe`, expiry and HMAC key rotation. Verify data API schema exposure and ownership checks for every new RPC.
4. Run exact migration against a **separate disposable Supabase test project** seeded with production-like schema and representative data. Collect before/after catalog diff and isolate HTTP E2E evidence. No production writes.
5. Require a separate explicit production migration approval, deployment window and rollback owner. Neither this PR nor a CI PASS constitutes authorization.

## Phased release (all stages independently approved)
A. Keep all production recovery writes disabled, source toggle OFF, general public toggle OFF. Confirm deployment SHA, preview authentication, current errors and production READ-ONLY status.
B. With separate approval, deploy migration **only**; immediately verify new functions' EXECUTE privilege and schema/catalog expectations. Still no new recovery routes/feature flags enabled.
C. Enable status-only checks for an individually authorized test account. Validate read-only response, owner/foreign JWT denied, revocation and expiration. Do not publish.
D. In a separately reviewed implementation, add server-side **bind and finalize** production paths using strict account allowlist + DB RPC authorization + trusted signer; implement safe client recovery and pre-upload immutable manifest bind. Require production-equivalent test evidence. Leave general public disabled.
E. Canary authorized accounts; validate interrupted upload, two tabs, stale journal, account switch, expiry, original SHA, storage object immutability and duplicate posts. Monitor, disable on anomaly.
F. Only after a distinct public-release approval, review independent server flags (`VIDEO_GENERAL_PUBLIC_RELEASE_APPROVED`, `VIDEO_PUBLIC_ROLLOUT_ENABLED`), production DB public rollout flag, RLS, rate limits, and user communication. Never use an empty allowlist as an implicit public release.

## Emergency stop and rollback
1. First disable recovery bind/finalize feature flags and publication server-side, while preserving already-published reads and owner hide operations. Keep client recovery OFF until server is proven ready.
2. Prefer **forward-disable**, not destructive DB rollback: retain immutable manifests, consumed nonces, reservations, original Storage bytes and posts. Never clear a browser transfer journal or auto-reupload a previously uncertain object to force recovery.
3. Revoke new EXECUTE privileges only when safe and after considering any in-flight transactions. Do not revoke existing application RPC or schema privileges.
4. If a SQL rollback is separately authorized, first check dependencies and row counts; use an explicit catalog-verified, transactional rollback plan. Never drop populated manifests or use CASCADE automatically.
5. Recheck denial for anonymous/foreign requests, preserved playback, ledger and posts, and audit log continuity.

## Known release blockers (2026-10-31)
- Production recovery table and RPCs absent.
- Production bind/finalize not implemented; current server is status-only.
- Client recovery feature is disabled; original journal protection must remain fail-closed.
- No authenticated Preview HTTP/UI smoke result due to deployment protection; READY/SHA and isolated E2E PASS are **not** equivalent to live user acceptance.
- Required storage-policy effective-permission audit and production-like migration dry run still pending.

## Verification record
Draft PR #132, previous HEAD `d677b46ee945b3ecff9b4b4a289a880ad4f09953`. Isolated CI: Video SQL `41025169742`, MOV `41025169769`, Poll-only `41025169932`, Storage HTTP `41025169747`: SUCCESS. Preview `dpl_BaJy1QPFUPy7x5NzA1N9KTgbn6if`: READY, SHA matched previous HEAD. Do not reuse old SHA proof after this documentation commit.


## 2026-10-31 production-read audit: high-priority findings
- The **authenticated INSERT** policies on `storage.objects` are permissive and OR-combined. `poker_post_videos_insert_once` allows an owner with a valid reservation without invoking `video_rollout_allowed()`; `video_rollout_storage_insert` separately checks the rollout flag. Therefore **turning the rollout DB flag off is not by itself a guaranteed Storage INSERT kill switch** under the currently deployed policy set. Do not rely on that flag as the only upload stop. A production policy change needs an independent security audit and separately authorized migration.
- The parent attested publisher checks `video_rollout_allowed()` both before and after locking, and checks the permanent reservation ledger and Storage generation. The candidate recovery wrapper relies on these protections.
- The current production `video_reserve_object_key` has 12/hour and 80/day per-owner reservation caps. Avoid destructive "retry by new key" behaviour.
- The candidate file `tests/video/recovery_production_candidate_NOT_APPROVED.sql` is **NOT** production-approved; its preflight rejects existing target migration objects rather than silently replacing them. This intentionally makes it fail-closed on rerun; it is not an idempotent installer yet. Before anyone applies SQL, complete a compatibility-safe idempotency design and production-like dry run.
- Server signing must use the existing production attestation key settings `VIDEO_ATTESTATION_KEY_HEX` and `VIDEO_ATTESTATION_KEY_ID` with an independently verified matching database key. Do **not** reuse `VIDEO_RECOVERY_ISOLATED_KEY_HEX` outside the disposable test environment. No production bind/finalize is enabled by this documentation change.

# Production video: limited rollout
Status: candidate only; no production mutation authorized or performed.

## Exact inputs
Base video PR #123: 7871c2481acb18fccf0a0f9c3d44d69b85c66a33.
Apply sql/video_production_limited_rollout.sql once, as one transaction, only to ephptepeuespnxtzdqby.
Do not apply cloud-test/QA SQL. Function name collisions abort rather than overwrite.
Preserve existing policies and grants; restrictive policies affect only video posts/post-videos.
Do not DROP or DELETE anything as rollback. No physical video deletion is enabled.

## Release prerequisites
The production profiles.poker_id=testplayer mapping was read-only checked against auth.users.id on 2026-10-30 JST and returned exactly one matching Auth user. Reconfirm the authenticated session ID before activation. Do not authorize by display name, mutable user metadata, or guessed UUID.
Use that single UUID in both VIDEO_ALLOWED_USER_IDS and video_private.allowed_publishers. The SQL ships with an empty allowlist and disabled settings.
Check existing Storage policies are accepted by the migration's conflict preflight. If it aborts, review the conflict; do not remove existing image policies to force application.
Run changed SQL and server gate tests, real JWT/Storage/HTTP end-to-end, full client build, and protected Preview matching the release SHA before production approval.
A synthetic SQL/JWT fixture is not proof of real Auth/Storage/browser integration.
Full production DB+Storage backup and complete restore are NOT available. An additive migration plus application rollback does not provide disaster recovery. Existing data restoration after an unexpected DB incident remains unproven.

## Environment manifest (no secret values)
Keep all flags off until approved.
Server-only:
- VIDEO_PRODUCTION_LIMITED_ROLLOUT=true only for the approved limited rollout.
- VIDEO_ALLOWED_USER_IDS=the verified testplayer auth UUID only.
- VIDEO_SERVER_ENABLED=true only after the default-off deployment smoke test.
- VIDEO_PRODUCTION_FENCED_READY=true.
- VIDEO_ATTESTED_RPC_RELEASE_APPROVED=true only after signed RPC/runtime verification.
- VIDEO_ATTESTATION_KEY_ID: provisioned smallint 1..32767.
- VIDEO_ATTESTATION_KEY_HEX: fresh CSPRNG 32-byte secret, matching video_private attestation key configuration; never VITE-prefixed.
- FFPROBE_BINARY_PATH: deployed absolute ffprobe executable, verified by Preview runtime attestation.
Existing nonprivileged connection: VITE_SUPABASE_URL must exactly equal https://ephptepeuespnxtzdqby.supabase.co and VITE_SUPABASE_ANON_KEY is the production public client key.
Client build: VITE_VIDEO_SERVER_ENABLED=true only for the reviewed release. It is UI availability, not authorization; server/DB deny all non-allowlisted users.
Server cloud-test configuration VIDEO_CLOUD_TEST_ENABLED, VIDEO_CLOUD_TEST_PROJECT_REF and VIDEO_CLOUD_TEST_VERCEL_PROJECT_ID must be unset (even the string false requests the cloud-test guard). Client VITE_VIDEO_CLOUD_TEST_ENABLED must remain false/unset. Do not use service_role or QA fixed HMAC secrets.
Provision the key into the existing private key table through a separately approved secret-safe path; do not put it in SQL files, shell arguments, CI logs, PRs or chat.

## Approved execution order (approval still required)
1. Capture read-only counts/policies/schema baseline and existing main deployment SHA.
2. Apply the reviewed SQL transaction. Verify normal posts/images/auth read paths, allowlist empty, settings disabled, private bucket and restrictive policies.
3. Provision the paired private DB/server key; add the verified testplayer UUID to both allowlists without enabling settings.
4. Integrate PR #130 into PR #123, then merge only the reviewed final SHA to main after approval. Restore Vercel's production build permission only as part of the approved deployment.
5. Deploy with VIDEO_SERVER_ENABLED=false and DB settings.enabled=false. Confirm existing site unchanged and video mutation denied.
6. After protected exact-SHA Preview E2E and final approval, enable DB settings and server video flag for testplayer only.
7. Verify testplayer reserve/upload/signed finalize/single post/playback, other user rejection, invalid JWT rejection, hide, new-post stop, existing image/post/login regression.
8. General public rollout is a separate authorization/policy review; do not broaden either allowlist automatically.

## Non-destructive rollback / moderation
Stop new DB reservations, Storage INSERT and finalize immediately:
UPDATE video_private.rollout_settings SET enabled=false WHERE singleton=true;
Then set VIDEO_SERVER_ENABLED=false in Vercel and redeploy the same safe version. Client flag changes require a build.
With limited-rollout target/allowlist settings retained, an authorized member can still call video_hide_own through the hide API while the server publication flag is false. SQL owner hide does not require settings.enabled.
Emergency admin hide (approved operator, parameterized UUID):
INSERT INTO video_private.hidden_videos(post_id) VALUES (the_verified_video_post_uuid) ON CONFLICT DO NOTHING;
Never paste an unverified identifier or modify normal posts. The RPC checks owner and video type. Hidden video metadata is filtered by posts RLS, Storage SELECT is denied and media API stops serving it. Already downloaded bytes cannot be revoked.
Retain posts, reservations, nonce records, hidden records and Storage objects. Do not drop columns/functions/policies while clients may use them.
If an application regression occurs, restore the recorded prior Vercel deployment with video off. Do not revert existing data or remove migration objects.

## Implemented boundary regression
The production adapter runtime regression uses real ffprobe and a strict mock HTTP transport (never production network), independently verifies the emitted HMAC/RPC claims, rejects server/DB non-members, rejects new publication while stopped, permits owner hide during stop, and rejects target mismatch before I/O. The separate disposable real Auth/PostgREST/Storage test validates actual SQL/RLS and signatures. Neither is a claim of completed production or Safari E2E.

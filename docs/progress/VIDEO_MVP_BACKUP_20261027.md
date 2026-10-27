# Video MVP release and private backup verification
Updated: 2026-10-27 15:12 JST

## Acceptance recorded before modification
- Export must refuse credential forwarding through redirects before any redirected request.
- Bound network response reads, create private files without a permissive creation window.
- Preserve bucket configuration and object metadata; detect changed or duplicate inventories.
- Verify exported byte sizes, SHA256 and exact local file inventory.
- Production release requires actual DB + Storage backups and independent isolated restore evidence.
- No secrets or production user content in GitHub, CI output or artifacts.

## Evidence
Start HEAD: fb390c3d5f7a7b759a685a968e909390fd6841b3.
All completed successfully: Video SQL 40459316530, Storage HTTP 40459316385, Poll-only 40459316216.
Read-only Supabase check: intended project ephptepeuespnxtzdqby, current_user postgres, 4 buckets / 7 objects.
These counts are inventory evidence only, NOT an export.
Local: python3 -m py_compile scripts/video_private_storage_export.py PASS.
Local: python3 -m unittest discover -s tests/video -p test_private_storage_export.py -v PASS (5 tests).
No full repository checkout/dependencies available locally; npm build/lint not executed locally.

## Changes
scripts/video_private_storage_export.py: redirect handler rejects redirects before forwarding credentials; bounded reads; recursion/name checks; private O_EXCL creation + fsync; bucket/object metadata preservation; before/after inventory comparison; offline --verify.
tests/video/test_private_storage_export.py: redirect, response bounds, checksum/exact inventory, symlink and duplicate regressions.
No application runtime or production schema changes.

## Remaining limitations
An unchanged before/after listing is not a transactional snapshot. Concurrent writes, deletions or replacements can still invalidate a recovery point. Establish a coordinated write-free backup window and correlate DB storage metadata with exported inventory before approval.
Local SHA verification is not a remote restore test. A 100 MiB object cap fails the entire export; it never proves completeness for larger objects.
Export output contains private user data and must remain outside GitHub/CI/Library artifacts. No backup output was created in this task.

## Blockers and exact next operations
The connected Supabase tools expose SQL but no Storage byte download or DB dump stream. No trusted DB connection credential or Storage export credential is provisioned to this runner. Do not retrieve secret keys using SQL, Vercel environment inspection, or alternate privileged paths.
The environment has no pg_dump/psql/docker/gh executables. GitHub clone is unavailable; source was accessed through the authenticated GitHub connector.
Owner/operator must use a trusted local VS Code terminal:
1. Obtain a complete private DB backup using Supabase's supported dump workflow, including application/auth data, schema, policies/functions/grants and required roles. Preserve restore prerequisites; never paste secrets into chat.
2. Download the reviewed scripts/video_private_storage_export.py from this branch and run python3 scripts/video_private_storage_export.py. Enter the service-role key only into its hidden local prompt. Output is under ~/PokerID-Private-Backups/.
3. Run python3 scripts/video_private_storage_export.py --verify <absolute-export-directory>.
4. Restore the DB and every Storage object to an isolated existing/local target (no paid project creation), preserving bucket configuration, content types and required ownership metadata through supported interfaces. Download restored bytes and compare every SHA256, size and object count, then validate auth/RPC/RLS.
5. Provide only sanitized results and recovery-point timestamp/count/checksums, or provision approved scoped access. Never send DB dumps, credentials or private objects in chat.
Only after these pass: provision production HMAC keys, apply reviewed RPC/RLS/Storage changes, configure Vercel gates, merge PR #123, deploy and perform authorized test-account upload/playback QA.
No production DDL/DML, key provisioning, Vercel configuration, main merge, production deploy or production browser QA performed.

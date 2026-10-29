# Manual video MVP production backup gate (operator review)

Scope: stand-alone change, no PR #123 HEAD mutation, no production SQL, merge or deployment.

## What is implemented

- Manual `workflow_dispatch` only. It cannot start on PR push.
- Protected GitHub environment `production-backup` intended to require a human reviewer.
- Read-only PostgreSQL 17 logical custom-format DB dump and Supabase Storage downloads for all four buckets / seven objects.
- Per-object SHA-256 manifest, DB SHA-256, inventory double-listing to detect path changes (does NOT guarantee an atomic data snapshot).
- Encrypt with an **age public recipient** before offsite transfer. No raw dump or object content is uploaded as Actions artifacts.
- Upload ciphertext to an **existing privately configured** S3 destination. Exit with error if a required setting is missing.

## Required configuration (not set by this PR)

GitHub environment: `production-backup`, protect with required reviewers and restrict deployments to trusted main branch.

Secrets (configure only in GitHub settings; never in issue/chat):
- `PROD_DB_URL`: PostgreSQL session pooler/direct TLS URL; read-only DB user with the necessary schema access, **NOT service role**.
- `PROD_STORAGE_READ_KEY`: privileged backup-only Storage read credential; review key privilege scope. Existing Supabase service_role is broad and must be treated as highly sensitive; do not grant to untrusted PRs.
- `BACKUP_AWS_ACCESS_KEY_ID` and `BACKUP_AWS_SECRET_ACCESS_KEY`: tightly scoped write-only access to an EXISTING private bucket.

Environment variables:
- `PROD_SUPABASE_URL`: the correct production HTTPS project origin (not test).
- `BACKUP_AGE_RECIPIENT`: trusted age public recipient. **Keep the corresponding private identity offline** for recovery.
- `BACKUP_S3_URI`: existing private `s3://bucket/prefix` location.
- `BACKUP_AWS_REGION`: correct configured storage region.

**Cost:** S3 storage, transfer and API requests may incur charges. Do not configure or run until the existing destination is confirmed to have zero incremental cost. The workflow does not provision resources.

**Important:** `workflow_dispatch` only runs a workflow file present on the repository default branch. Review and merge this separate backup PR on its own first, only after confirming workflow permissions, trusted dependencies and the protected environment configuration. Do not merge PR #123 or enable production video flags as part of this step.

## Explicit NO-GO limits

- No backup has run just because this workflow exists.
- DB logical dump is not a complete Supabase platform recovery point: secrets, project configuration and compatible restore conditions need separate checks.
- Storage files are backed up, but restored Storage API behavior and authorization are not proven by SHA alone.
- Concurrent writes could cause inconsistency between DB and Storage. Before certifying, compare both against a verified quiescent snapshot or repeat with controlled maintenance window.
- This workflow does **not** perform an isolated restore. The encrypted archive must be retrieved, decrypted in a safe isolated environment, the DB restored to a compatible clone, all object bytes restored and compared by hash, and auth/RLS validated. Store the restore PASS log outside the repository; do not include credentials or customer data.
- Failed/missing configuration, mismatched inventory, incomplete export, failed upload or failed restore = NO-GO.
- `VIDEO_SERVER_ENABLED` and related production release gates must remain OFF until separate release checks pass.

## Operator checklist

1. Configure the protected environment, least-privilege secrets, age public recipient, existing zero-incremental-cost private storage and offline key custody.
2. Review the backup PR, merge only the backup changes to main. Leave PR #123 untouched.
3. Trigger `Manual encrypted production backup` through GitHub Actions. Verify successful remote encrypted object delivery.
4. Independently obtain and decrypt the object in a trusted environment, run full isolated DB restore and Storage byte restore, compare manifest/hash and exercise auth/RLS.
5. Record proof and then continue with video production schema/RPC/Storage/HMAC staging and authorization QA. Do not equate the backup workflow's success with deployment approval.


## Isolated restoration smoke test

After downloading the encrypted S3 backup into a trusted private machine, decrypt it locally with the offline age identity. Keep the resulting directory private, outside any repo. The decrypted directory must contain `database.dump`, `database.sha256`, and `storage/storage-manifest.json`. Run:

```bash
python3 scripts/video_verify_backup_bundle.py "/private/path/to/decrypted"
bash scripts/video_verify_isolated_db_restore.sh "/private/path/to/decrypted"
```

The second step starts a throwaway PostgreSQL 17 Docker container with `--network none`, restores with `pg_restore --exit-on-error --single-transaction`, checks local SQL access, and removes it. **This is only a PostgreSQL logical restore smoke test.** It is NOT a full Supabase backup/restore of Auth, Storage, managed settings, extension behaviour, privileges, or live service interactions. Passing either command does not authorize production deployment. A complete staging-equivalent Supabase data and Storage API restoration with auth/RLS tests is still required.

## Safety limitations discovered during review

- A repository-scoped GitHub Actions secret is not equivalent to a protected environment secret. Place production credentials **only in an explicitly protected `production-backup` environment**, and restrict the eligible branch/reviewers. Public repositories and code from unreviewed PRs must never receive production credentials.
- Current workflow depends on an **existing private S3 bucket**. We have not confirmed one exists or that its incremental storage/requests/egress cost is zero. Without this, job must remain unrun.
- The job uses a pinned Supabase origin and stops on a Storage redirect to another host. Some providers legitimately redirect downloads; this must be tested against an authorized non-production bucket before production backup.
- `EXPECTED_STORAGE_OBJECTS=7` and `EXPECTED_STORAGE_BUCKETS=4` are current inventory preconditions, not permanent constants. Any change means a deliberate inventory reconciliation, not a blind reset.
- The current restore smoke test is neither fully exercised nor independently reviewed. Do not merge or trigger the backup workflow merely because the source files have been added.

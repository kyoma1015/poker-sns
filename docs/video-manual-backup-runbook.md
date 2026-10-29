# Manual video MVP production backup gate (operator review)

Scope: stand-alone change, no PR #123 HEAD mutation, no production SQL, merge or deployment.

## What is implemented

- Manual `workflow_dispatch` only. It cannot start on PR push.
- Protected GitHub environment `production-backup` intended to require a human reviewer.
- Read-only PostgreSQL 17 logical custom-format DB dump and Supabase Storage downloads for all four buckets / seven objects.
- Per-object SHA-256 manifest, DB SHA-256, inventory double-listing to detect path changes (does NOT guarantee an atomic data snapshot).
- Encrypt with an **age public recipient** before offsite transfer. No raw dump or object content is uploaded as Actions artifacts.
- Upload ciphertext only to a 1-day GitHub Actions artifact for manual download. This is transient transport, never a permanent backup.

## Required configuration (not set by this PR)

GitHub environment: `production-backup`, protect with required reviewers and restrict deployments to trusted main branch.

Secrets (configure only in GitHub settings; never in issue/chat):
- `PROD_DB_URL`: PostgreSQL session pooler/direct TLS URL; read-only DB user with the necessary schema access, **NOT service role**.
- `PROD_STORAGE_READ_KEY`: privileged backup-only Storage read credential; review key privilege scope. Existing Supabase service_role is broad and must be treated as highly sensitive; do not grant to untrusted PRs.

Environment variables:
- `PROD_SUPABASE_URL`: the correct production HTTPS project origin (not test).
- `BACKUP_AGE_RECIPIENT`: trusted age public recipient. **Keep the corresponding private identity offline** for recovery.

**Cost:** This workflow uses existing GitHub Actions and temporary Actions artifact storage; usage limits and possible additional billing must be checked for the repository before dispatch. No extra billing is authorized. Artifacts expire after 1 day, and must be downloaded and moved to independent private durable storage. A 1-day artifact is NOT a backup recovery point.

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
3. Trigger `Manual encrypted production backup` through GitHub Actions only after confirming remaining Actions budget; obtain the encrypted artifact within the 1-day retention period. Treat it only as a transfer.
4. Move the encrypted `.age` archive and separately safeguarded private age identity into independent durable PRIVATE storage (for example existing iCloud Drive on iPhone, after confirming available space and access restrictions), verify download integrity and keep a second independent copy. Do not upload the age private identity to Actions or GitHub.
5. Independently decrypt the object in a trusted environment, run full isolated DB restore and Storage byte restore, compare manifest/hash and exercise auth/RLS.
6. Record proof and then continue with video production schema/RPC/Storage/HMAC staging and authorization QA. Do not equate the backup workflow's success with deployment approval.


## Isolated restoration smoke test

After downloading the encrypted S3 backup into a trusted private machine, decrypt it locally with the offline age identity. Keep the resulting directory private, outside any repo. The decrypted directory must contain `database.dump`, `database.sha256`, and `storage/storage-manifest.json`. Run:

```bash
python3 scripts/video_verify_backup_bundle.py "/private/path/to/decrypted"
bash scripts/video_verify_isolated_db_restore.sh "/private/path/to/decrypted"
```

The second step starts a throwaway PostgreSQL 17 Docker container with `--network none`, restores with `pg_restore --exit-on-error --single-transaction`, checks local SQL access, and removes it. **This is only a PostgreSQL logical restore smoke test.** It is NOT a full Supabase backup/restore of Auth, Storage, managed settings, extension behaviour, privileges, or live service interactions. Passing either command does not authorize production deployment. A complete staging-equivalent Supabase data and Storage API restoration with auth/RLS tests is still required.

## Safety limitations discovered during review

- A repository-scoped GitHub Actions secret is not equivalent to a protected environment secret. Place production credentials **only in an explicitly protected `production-backup` environment**, and restrict the eligible branch/reviewers. Public repositories and code from unreviewed PRs must never receive production credentials.
- GitHub Actions runtime/storage quotas and private long-term destination space are unverified; without evidence of zero additional billing and a durable private destination, job must remain unrun.
- The job DOES NOT create a persistent backup destination. The temporary encrypted GitHub artifact is deleted automatically after 1 day; permanent private storage and retrieval proof must be arranged separately.
- The job uses a pinned Supabase origin and stops on a Storage redirect to another host. Some providers legitimately redirect downloads; this must be tested against an authorized non-production bucket before production backup.
- `EXPECTED_STORAGE_OBJECTS=7` and `EXPECTED_STORAGE_BUCKETS=4` are current inventory preconditions, not permanent constants. Any change means a deliberate inventory reconciliation, not a blind reset.
- The current restore smoke test is neither fully exercised nor independently reviewed. Do not merge or trigger the backup workflow merely because the source files have been added.

## Synthetic regression tests

Run `python3 -m unittest discover -s tests/video -p test_manual_backup_integrity.py -v` before approving PR #127. These tests exercise valid, tampered, missing, extra and traversal-path synthetic inputs. They do not touch production or prove live Storage download compatibility.

## Mandatory manual configuration on GitHub and iPhone

1. In repository Settings > Environments, create `production-backup`, require a trusted reviewer and restrict allowed deployment branches to `main` before storing production credentials. **Save the environment**.
2. In that environment only, set secrets `PROD_DB_URL` and `PROD_STORAGE_READ_KEY`; set variables `PROD_SUPABASE_URL` (production HTTPS URL) and `BACKUP_AGE_RECIPIENT` (offline-generated public recipient). **Save each secret/variable**. Never paste secret values into chat or source code.
3. Verify existing GitHub Actions included minutes/artifact quota before manually running from main. The artifact is encrypted but can be accessible to repository viewers; confidentiality depends on keeping the corresponding age private identity strictly offline.
4. From the GitHub Actions run, download the `.age` ciphertext within one day; on iPhone save to an existing private durable location such as iCloud Drive after checking capacity. Keep the age identity separately and test decryption in a trusted environment.
5. A successful Actions run alone is **not proof of recovery**. Full compatible DB and Storage bytes restoration, user/session authorization and RLS must pass independently before production promotion.

## GitHub public-repository billing review (2026-10-29)

GitHub's official documentation states that **standard GitHub-hosted runners on public repositories are free**. This repo is public and the workflow uses `ubuntu-latest`, so these compute minutes do not require paid hosted runners. Artifact storage has separate quotas: GitHub Free includes **500 MB shared artifact storage**, subject to account-level existing usage. The workflow now refuses to upload archives larger than 200 MiB, but that **does not establish available headroom** or prevent account-level billing settings from permitting paid overages. Before dispatch, check account **Settings > Billing & licensing > Usage / Budgets** and configure stop-usage budgets as appropriate. No current billing usage can be read by the installed GitHub connector.

Official docs: https://docs.github.com/en/billing/concepts/product-billing/github-actions ; https://docs.github.com/en/billing/reference/product-usage-included

**GitHub secret configuration cannot be completed with the current connected GitHub actions** (no environment/secret management action). A user with repository administrator permission must do the one-time environment setup in GitHub's UI. The workflow must be merged to default branch before its first manual dispatch. Do not merge until the workflow is reviewed and the protected environment has been configured.

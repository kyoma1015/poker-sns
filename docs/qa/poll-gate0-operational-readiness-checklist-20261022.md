# Poker ID poll-only Gate 0 — operational readiness and independent approval checklist

**Status: Gate 0 BLOCKED / Gates 1–10 BLOCKED / publication NO-GO.**
**Scope: documentation-only.** This document is not authorization to connect to production Supabase, create/export backups, restore, generate or transfer real secrets, execute SQL, change Vercel, purchase services, or touch GTO/controller. Any future action requires separate, explicit, scope-specific authorization.

## 1. Single source of truth and ownership

- This file is the **Gate 0 operational-readiness checklist only**. The canonical release authorization and 11 gates remain in [poll-final-owner-approval-checklist-20261022.md](poll-final-owner-approval-checklist-20261022.md); the release runbook and feasibility study retain their own scope.
- Product owner: **TBD**; recovery operator: **TBD**; secret custodian: **TBD**; independent technical reviewer (different from operator): **TBD**; incident contact: **TBD**.
- Record sign-off privately: date/time, scope, reviewer identity, evidence path and immutable digest, expiry, explicit permission and any rejected risks. Do not put signatures, personal details, credentials, ciphertext of actual backups, real responses, Vault keys or sensitive logs in GitHub.
- Change freeze, maintenance window, exact SQL candidate SHA256 and rollback/stop contact are **unapproved placeholders**, not granted authorizations.

## 2. Owner decisions — minimum necessary; no Mac required now

| ID | Decision or verification | Required acceptance evidence | Owner / reviewer | State |
|---|---|---|---|---|
| G0-01 | Identify available recovery machine or service (Mac **not mandatory**) | Platform, OS, free capacity, availability and ability to run compatible PostgreSQL 17 + required extensions; verified separately, not inferred from GitHub runners | Recovery operator / reviewer | BLOCKED |
| G0-02 | Identify an independent physical or administrative backup destination | Medium/location, ownership, access control, separation from recovery host, sufficient free capacity, offline/offsite availability and replacement/failure plan | Storage custodian / reviewer | BLOCKED |
| G0-03 | Agree private age key custody | Key generation only after separate approval, recipient public key, primary secret-key custodian, independent sealed recovery copy, access and revocation/rotation policy; never co-locate sole key copy with ciphertext | Secret custodian / reviewer | BLOCKED |
| G0-04 | Approve retention and recovery objectives | 30-day rolling retention policy; RPO <= 24h and RTO <= 24h as **objectives**, backup frequency, alert owner and missed-run escalation | Product owner / reviewer | BLOCKED |
| G0-05 | Appoint independent reviewer and incident operator | Named independent technical reviewer and reachable escalation/stop contact; evidence access without secrets | Product owner / reviewer | BLOCKED |
| G0-06 | Define freeze, scope and separate approvals | Scope of database, roles, extensions, migrations, Vault, Storage bytes, Auth and external integrations; change window and explicit separate Gate 1+ authorization protocol | Product owner / reviewer | BLOCKED |

Do not require a Mac merely to complete the document. Hardware, storage and key-custody facts cannot be asserted by GitHub CI.

## 3. Future operating procedure (DESIGN ONLY; DO NOT EXECUTE)

### A. Backup preparation and key separation
1. Operator and independent reviewer agree a source inventory: database roles/schema/data plus dependent posts, polls, historical questions, responses, notifications, RLS/grants/functions/triggers, migrations/extensions, Vault, Storage object **bytes** and Auth/external configuration. Logical DB export alone does **not** capture every dependency.
2. After separate written permission, create age identity privately in an authorized secure environment. Store the **secret identity** with a custodian and independently protected recovery copy; record only recipient public key and non-sensitive fingerprints in operational documentation. Never place real keys in GitHub Actions, repository, logs, chat, or the same sole storage location as encrypted backups.
3. Encrypt before transfer to an independently controlled destination; stage incomplete outputs separately. Record source timestamp, tool versions, encrypted-file SHA-256, size, generation ID and storage location in a **private** manifest.
4. Mark a recovery point VERIFIED only after successful copy, digest parity and a separately authorized decrypt/integrity verification. A SHA-256 match alone is not proof of restore usability.

### B. Retention, RPO and RTO
1. Target at least one successful, **verified** recovery point every 24 hours. Missing/late jobs trigger an alert and escalation; never silently treat a stale point as current.
2. Retain verified generations within the preceding **30 days**. Before any prune, verify an independently restorable latest valid point. If no verified point exists, **STOP deletion**; preserve the most recent verified point even when older than 30 days, subject to a documented exception and storage-risk review.
3. Avoid deleting the last recoverable generation on an incomplete, corrupted, interrupted or unverified backup. Failed new generations are not promoted; keep prior verified generations.
4. RPO <= 24h is measured against the actual age of the latest **usable** recovery point and gaps in successful generations; RTO <= 24h requires a timed full recovery rehearsal, including dependent services, not just a timestamp comparison.
5. A 30-day retention policy is a target to implement and verify, not evidence that 30 days of backups currently exist.

### C. Failure stop and controlled resumption
1. **STOP** on missing/incorrect age key, failed digest/decrypt, insufficient capacity, missing Storage bytes, restore mismatch, unexpected external callback, privacy/RLS regression, stale RPO, or unverified RTO.
2. Quarantine failed artifacts and protect previous verified recovery points. Preserve only redacted logs, exit codes, timestamps and digests in private evidence. Do not print secret keys, raw vote identities, or plaintext.
3. No automatic retry that deletes old backups, resumes cron, re-grants RPC privileges, or re-enables public access. Operator investigates; independent reviewer verifies root cause and safe rollback/re-enable plan.
4. For future authorized production incident handling, follow [poll-release-go-no-go-gates-20261022.md](poll-release-go-no-go-gates-20261022.md) and the separate SQL approval process. The emergency `disable_candidate.sql` is a **feature stop**, not a database restore, and running cron jobs still require drain verification.

## 4. Evidence and approval matrix — no implied PASS

| Evidence class | Current supported evidence | What remains unverified |
|---|---|---|
| Synthetic age operations | PR #92; CI [39745333770](https://github.com/kyoma1015/poker-sns/actions/runs/39745333770): 7 PASS | Real key custody, actual external media, production decryptability |
| Synthetic retention/RPO/RTO predicates | PR #94; CI [39746532560](https://github.com/kyoma1015/poker-sns/actions/runs/39746532560): 10 PASS | Actual 30-day history, actual 24h recovery points, timed full recovery |
| Synthetic integrated lifecycle | PR #95; CI [39750185267](https://github.com/kyoma1015/poker-sns/actions/runs/39750185267): 12 PASS; artifact 12412659169, SHA256 `530006089549ddacd61436e257fc10c8e22ece27e105f0c3ebdf93b49108ae6f` | GitHub runner 'offsite' is merely a separate directory; no physical separation or production data |
| Isolated poll regression | PR #95; CI [39750185169](https://github.com/kyoma1015/poker-sns/actions/runs/39750185169): 70 PASS; artifact 12413660723, SHA256 `6e610618ae5f3f31d4b4ad54f1559b5ae1dfa976075e1870ce031d8ab95f96b3` | Real production-equivalent restored data and dependencies |
| Production gates 0–10 | **All BLOCKED** | Owner/independent reviewer sign-off, actual backup and complete isolated restore, Vault, Storage, Auth, live catalog, cron, SQL and deployment approvals |

Synthetic test counts are separate suites; they are **not production gate passes**.

## 5. Private Gate 0 sign-off record (blank by design)

- Scope / source / change freeze: **UNAPPROVED**
- Recovery operator / key custodian / storage custodian / independent reviewer: **TBD**
- Hardware or service / storage independence / capacity: **UNVERIFIED**
- age key custody / offline recovery copy / rotation: **UNVERIFIED**
- 30-day retention / 24h RPO / 24h RTO acceptance and exception handling: **UNVERIFIED**
- Emergency stop contact and escalation: **TBD**
- Private evidence identifiers, SHA-256, reviewer timestamp: **NOT PROVIDED**
- Product owner approval: **NOT GRANTED**
- Independent reviewer approval: **NOT GRANTED**
- **Gate 0 decision: BLOCKED. Release decision: NO-GO.**

Passing Gate 0 after future review would **not** authorize Gate 1 production backup, Gate 2 restore, Gate 9 SQL writes, or Gate 10 Vercel/publication. Each requires its own explicit approval.

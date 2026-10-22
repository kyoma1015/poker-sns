# Poker ID — poll-only final GO/NO-GO and owner authorization (2026-10-22)

**Status: NO-GO. Documentation and review only.** Baseline: main after PR #90 merge `5390caf29f5f3a0c7e5c46fb67b7239b7bfa7a13`. This checklist **does not authorize** a production connection, backup, restore, SQL execution, Vercel action, paid service, or GTO/controller change. Every production action requires a new explicit scope-specific authorization. Historical production observations are **not** current facts.

## Evidence classification

- **Synthetic PASS:** PR #77 synthetic PG17 dump/restore; #78 PG17 extension availability; #79 synthetic Vault/cron runtime; #87–#88 synthetic old/new cron cutover and failure handling; #89 real candidate `poll_private.close_due_polls()` on synthetic fixture with two connections, dedupe and rollback; #90 real PostgREST role-matrix, 70 PASS / 0 FAIL / 0 BLOCKED, run [39738936406](https://github.com/kyoma1015/poker-sns/actions/runs/39738936406), artifact `12408596232` SHA256 `8dcc0e6a0fc6395ab088c72fd4a5094d56246cf566e20935378373ff7e179ad5`. #76 is a threat model; #86 release gate documentation. These are **not production PASS**.
- **Historical read-only snapshot:** PostgreSQL 17.11; 8 polls and 4 historical questions; 7 Storage metadata objects; 19 migrations; legacy cron `poker_id_poll_closed_notifications` calling `public.dispatch_poll_closed_notifications()`; historical `poll_private` absent. Re-verify under a separate future read-only authorization.
- **Unverified:** real backup, full isolated restore, Vault key portability, Storage bytes, Auth/external dependencies, current catalog/RLS/RPC, live cron drain, maintenance and production release. **BLOCKED** until individually evidenced.

## Eleven independent gates (0–10) — all required for GO

| Order | Gate | Owner / reviewer | Minimum private evidence to pass | Stop / NO-GO condition | Potential zero-extra-subscription route |
|---|---|---|---|---|---|
| 0 | Authorization & change freeze | Product owner + independent reviewer | Written scope, authorized operators, maintenance window, approved exact SQL hashes, RPO/RTO, stop contacts, separate approval for each production action | Any missing approval, unclear data custody, concurrent uncoordinated migration | Documentation and GitHub review only: yes |
| 1 | **Real private backup** | DB owner / independent recovery reviewer | Owner-approved export, source/time, tool versions, encrypted artifact, protected storage and TTL, SHA256, complete dependency and role/extension/migration coverage; no secrets or voter records in CI | No verifiable backup or missing dependency | CLI logical export + local storage may avoid paid cloud tiers, **not yet proven**; no execution under this task |
| 2 | **Full isolated restore** | Recovery operator + independent reviewer | Disconnected PG17-compatible restore exit 0, FK/count/hash parity, posts, polls, historical questions, responses, profiles, notifications, roles, grants, RLS, RPCs, triggers, extensions; side effects disabled | Partial restore, mismatch, unexpected outbound callbacks, missing roles | Local Docker potentially free excluding machine/storage costs; requires separate permission |
| 3 | **Vault production-key compatibility** | Secret custodian + independent reviewer | Approved secure key transfer, isolated decrypt compatibility attestation without exposing plaintext or keys; rotation/recovery plan | Cannot decrypt required secrets, key custody unclear | Synthetic Vault test free but **does not clear** this gate |
| 4 | **Storage bytes** | Storage owner + recovery reviewer | Bucket policies and metadata/object-byte reconciliation, secure isolated retrieval/restore, count/digest verification, access checks | Only metadata recovered, missing object bytes, access-policy regression | Local encrypted object export potentially free; actual feasibility unknown |
| 5 | **Auth and external dependencies** | Auth/integration owner + reviewer | Inventory and independent checks of Auth users/config/providers, secrets, SMTP, Edge Functions, webhook targets, Storage/Auth role bindings; outbound delivery disabled during rehearsal | Missing or unsafe dependency; production callbacks from restore | Inventory/review free; actual restore may need separate services |
| 6 | **Fresh live catalog & RLS/RPC** | DB owner + security reviewer | Authorized read-only snapshot immediately before change: every interactive RPC overload, SECURITY DEFINER/INVOKER, effective EXECUTE/USAGE, policies/grants, legacy rows and vote/notice digests; owner/voter/observer/anon real-role acceptance on isolated restored data | Unknown overload, anonymous identity exposure, missing restrictive policies, historical-data mismatch | Read-only queries may be free; **not authorized in this task** |
| 7 | **Legacy cron stop & in-flight drain** | DB owner + scheduler reviewer | Current cron job IDs/commands/status, separately approved retirement of legacy job, zero in-flight poll jobs after drain, one new scheduler only after approved `schedule_candidate.sql`, dedupe proof | Any old or running worker, overlapping schedules, ambiguous job | PG cron existing extension; no extra subscription assumed |
| 8 | **Emergency stop and controlled re-enable** | Incident owner + independent reviewer | On restored production-equivalent data: `disable_candidate.sql` stops both known jobs, denies RPCs, preserves votes/posts/receipts; in-flight drain observed; reviewed explicit re-grant and schedule procedure tested | Data loss, exposed RPC, cron resumes without approval, incomplete drain | Isolated rehearsal potentially free |
| 9 | **Separate SQL release authorization** | Product owner + DB operator + independent reviewer | Signed exact candidate choice (**forward OR core**, not both as cumulative migrations), checksum, validated rehearsal, release window, rollback contacts, fresh backup, approval of any optional legacy-question guard | Any preceding gate BLOCKED, unsigned SQL, change drift | Approval/review free; production execution **not authorized** |
| 10 | **Separate Vercel/publication authorization** | Product owner + deploy operator + reviewer | Distinct approval after safe DB migration and acceptance; verified deployment target, version, monitoring, emergency rollback, user communication | No explicit Vercel approval, failed smoke test, privacy regression | Review free; **deployment prohibited now** |

## Exact decision protocol

1. Mark each gate **BLOCKED** by default. A synthetic PASS never changes a production gate to PASS. Record reviewer, date, evidence location, immutable SHA/digest and expiry of evidence privately.
2. A gate moves to PASS only when its responsible owner and independent reviewer both sign the evidence. Any failed restore, lost object, privacy leakage, unresolved running cron, unexpected cost or unauthorized action is **STOP / NO-GO**.
3. Approvals are sequential: scope approval **does not itself permit** backup, backup approval does not permit restore, restore approval does not permit SQL writes, and SQL approval does not permit Vercel deployment. Each requires separate explicit user authorization.
4. Immediately before a future authorized maintenance window, refresh live catalog and cron evidence; stale historical counts and the synthetic fixtures cannot be used as current production facts.
5. If a release rehearsal fails: stop, preserve evidence, do not weaken `schedule_candidate.sql` guards, do not automatically restart cron or replay legacy notifications, and do not use destructive schema rollback. Re-enable only after root cause, restored-data parity, explicit grants, and new approval.

## Sign-off template — unapproved placeholders

| Approval | Authorized scope and environment | Owner signature/date | Independent reviewer/date | Evidence SHA/location | Status |
|---|---|---|---|---|---|
| Backup only | Not granted | — | — | — | BLOCKED |
| Isolated restore only | Not granted | — | — | — | BLOCKED |
| Live read-only catalog | Not granted | — | — | — | BLOCKED |
| Legacy cron maintenance | Not granted | — | — | — | BLOCKED |
| Production SQL writes | Not granted | — | — | — | BLOCKED |
| Vercel deployment/publication | Not granted | — | — | — | BLOCKED |

**Cost constraint:** No paid Supabase/PITR/cloud restore/project duplication may be purchased without a separate cost approval. "Potentially free" means no additional subscription is identified, **not** guaranteed zero cost or proven feasibility.

## Sources and unchanged candidate files

- `docs/qa/poll-release-go-no-go-gates-20261022.md`
- `docs/qa/issue22-poll-production-release-runbook-20261022.md`
- `docs/qa/poll-backup-isolated-restore-feasibility-20261022.md`
- `sql/poll_only/forward_candidate.sql`
- `sql/poll_only/core_without_notifications_candidate.sql` (alternative)
- `sql/poll_only/block_legacy_question_inserts_candidate.sql` (optional separate review)
- `sql/poll_only/schedule_candidate.sql`
- `sql/poll_only/disable_candidate.sql`
- `tests/polls/verify_backup_restore.sh` (**three synthetic tables only**, not full restore)

**Final decision: NO-GO until all eleven gates have private, current, independently reviewed evidence and separately authorized production actions.**

## Synthetic gate-0 evidence addendum — 2026-10-22 (no gate status change)

- PR #92 merged at `8a3b786a64d82455cb61af4b07c9a701bf63f8f8`: synthetic age key generation, encryption, decrypt/roundtrip, ciphertext SHA-256 copy parity, key separation, wrong-key/tamper rejection and marker nonexposure; [run 39745333770](https://github.com/kyoma1015/poker-sns/actions/runs/39745333770), **7 PASS / 0 FAIL / 0 BLOCKED**. This is not an actual offsite storage or real backup test.
- PR #94 merged at `9c6e65c18297bea59a1db2366ef27ac4e8259596`: synthetic 30-day retention, verified-generation preservation, RPO/RTO 24-hour boundary *predicates*, SHA-256 mismatch, missing key, insufficient capacity, interrupted copy and synthetic logging; [run 39746532560](https://github.com/kyoma1015/poker-sns/actions/runs/39746532560), **10 PASS / 0 FAIL / 0 BLOCKED**. These predicates do not measure actual restoration time.
- This PR adds an integrated synthetic age lifecycle test and isolated workflow, with actual outcome, run ID, artifact ID and SHA-256 to be recorded **only after CI completion**. The test creates throwaway synthetic keys/data on a GitHub runner; staging/offsite are separate directories on the same runner, **not** physically independent storage.
- Evidence classification remains **synthetic PASS only**. No production source access, encrypted real backup, disconnected full restore, actual Vault/Storage/Auth recovery, private key custody verification, independent review or owner authorization has occurred.
- **Gate 0 = BLOCKED; gates 1–10 = BLOCKED; publication = NO-GO.** No approval or production action is implied by this addendum.

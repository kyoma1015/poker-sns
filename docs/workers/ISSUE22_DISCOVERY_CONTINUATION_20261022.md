# Issue22 bounded discovery continuation — 2026-10-22

Verdict: CONDITIONAL PASS. Three actual new source tasks, original state retained; no live controller/scheduler adoption or production release. This is a finite host invocation, not an independently proven scheduled coldstart. Provider runID UNKNOWN; no schedule registration/extension or CLI/auth bypass.

## Fresh gates and completed source
Observed main: `4ebcad2022d859ccd098562bf70065d9042fbfbf` (external PR95 merge). PR38 reviewed code stays `dadf4d82b24fd166f15f291724cb6ac0c35d3974` before this evidence-only update. Existing PR80–85 exact heads and all Actions successes were reread. Fresh complete paginated open-PR base/head/files snapshots used strict PR38 exact-ancestor/blob/ancestor-blob/reverse-patch proofs. No filename-only exemption. Original4 spec_hash continuity verified, no source task replay.

| Lane | New source | Immutable baseline → result | Draft / CI |
|---|---|---|---|
| A | scripts/continuation_recovery.py: durable non-executable suggestions, owner/status, digest dedup, cap1000 atomic batch |49 tests/9 missing-API ERROR →49PASS; worker22/queue15PASS| PR96 /39767309432 SUCCESS |
| B | src/tdaQuizData.ts + src/TDA.tsx: normalize optional filter strings before React rendering |28 tests/23PASS5FAIL →28PASS, including4 actual mobile browser cases; oldsearch16/savedanswer14/audit18; types/Vite/lintPASS | PR98 /39768283251 SUCCESS |
| C | gto/hand169.py: exponent-scaled weighted EV avoids intermediate underflow |42 tests/2FAIL →42PASS including Decimal oracle5; GTO40PASS| PR97 /39767319480 SUCCESS |
| D | no duplicate source created |Existing PR30 patch missing from PR82 audit source. Fixed53 has48PASS5FAIL. Exact old12-line patch forward-applies, reverse-check fails: not inherited.| Existing PR30 retained; new input65901ec358ac75ec7aaea250800b7acfdbb7b0a3 saved, not a new implementation |

Source tasks used prepare_host_session → formal collaboration agent → observed completion → trusted host receipt → finish_host_session. Host rechecked fixed tests/protected hashes/source hashes/tamper/noop and committed. Private tokens/receipts/SQLite were not published. Retained counts after source: implemented32/blocked2/running0. New discovery schema is NOT installed in live retained state; only owned temporary SQLite tested. No controller hot switch.

Full source commits:
- A input `2f5faca8b0230c4afbff6fca10ca30a59e3bf918`, source/head `a3186ef6a5da4c3489aa2e7947fdea2b00395c31`; `codex/a-discovery-store-fix-20261022` → `codex/a-discovery-store-input-20261022`.
- B input `6b8610876b607920fffcbde7399b736aa27b6db7`, source `74ade9a2ebe844dab9874533dc49bb0905655f49`, CI-only head `8b1e0cf79160135bf69711abe69a2dffb8701a09`; `codex/b-filter-values-fix-20261022` → `codex/b-filter-values-input-20261022`.
- C input `599ef4c02d87d6e902f725bed3d9ac1f5bc466b2`, source `a4ced9e4e37e79e32a259ed28d2cfbe279542521`, CI-only head `322b3f3ad904074018d2b4e25acd319c0c9f6f53`; `codex/c-weighted-ev-fix-20261022` → `codex/c-weighted-ev-input-20261022`.

Separate CI-only host commits do not alter tested source or protected acceptance. Python changes do not require web builds. B CI runs npm ci/build/lint plus mocked browser suites; local equivalent type projects/Vite external output avoid changing protected worktrees. Existing lint/chunk warnings remain.

## Discovery/restart implementation and limits
PR96 extends the existing controller, not a second worker. discover(sources) uses existing bounded checkbox extractor and persists SHA256(lane/reference/title) metadata. Rediscovery preserves owner/status. BEGIN IMMEDIATE deduplicates concurrent insertions and rejects whole overflow batches above1000. Only review_required/blocked/dismissed statuses; no ready/running/implemented promotion. Anchor verification happens before additive schema. Public checkpoint never exports discovery text/owner. Leases, original finite run cap, preparation, protected tests and recovery remain unchanged.

Tests prove temp-state close/reopen, concurrent dedup, assignment validation, cap atomicity, no untrusted promotion and missing-state failure. They do not prove unattended hosting. `DISCOVERY_QUEUE_20261022.json` is a public, non-executable review handoff; it cannot recreate private leases or authorize implementation. The new runtime API is not yet called by the active controller. A reviewed bounded invocation adapter and explicitly approved controller adoption remain next work; fixed FAIL required before another source descriptor.

Existing continuous-queue-check.yml is a gated default-branch validation schedule, not a model/code-writing daemon. No new schedule, cost-bearing runner, token or secrets were created; original finite reservation counts/dates unchanged. Provider callback/coldstart and availability-limit detection/release remain unverified. Do not steal unknown-live expired leases; existing recovery gates still apply. Deployment of controller/queue changes needs separate owner approval.

## Reconciliation and honest failure records
C nonempty task already implemented as PR57; B/D old ready IDs already completed and were not replayed. D PR30's exact existing source must be reused in a reviewed integration input, not independently rewritten or merged twice. A preliminary discovery-v1 descriptor accidentally retained code_worker.py scope from its template; strict overlap gate rejected it. Its immutable hash is preserved with reconstructed matching JSON; corrected distinct v2 was reviewed/prepared. No same-ID rewrite or failed test suppression.

B source agent encountered one restricted child-process EPERM. It stopped that probe. Root used its existing authorized host execution and verified the actual four-browser acceptance, not a mock success or authentication workaround. D's initial command accidentally ran old48 tests in the old checkout; only the correct new-input53/5FAIL run is counted as baseline. The old artifact was untouched.

## Uncompleted work / no production claim
- B350 immutable official source snapshot/hash/clause review is still absent; no question accuracy/publication PASS.
- D36 expert semantic labels/classifier evidence absent; structural tests are not semantic accuracy. PR30 reuse is a known inheritance task, not a new invented bug.
- Original G11 ABI/checkpoint compatibility and real poker strategy convergence remain unproven. C synthetic aggregation oracle is not a solver correctness proof.
- Draft74/75,66/69/70 and all new Drafts remain unmerged. Main integration/controller switch require explicit approval. Poll/backups/PR93 etc belong to other owner and were not changed.
- No production Supabase/SQL/user data/Vercel/billing operations. Poll release NO-GO and existing Vercel403 remain.

Evidence: docs/qa/issue22-discovery-20261022 contains immutable candidates/plans/sanitized host results, original FAIL views with raw/published hashes, positive regression outputs, CI job test lines and state summary. Re-access named Git branches/full SHAs; retained originals remain in /workspace/work. Next invocation must reread main/PRs/lease/state, not replay implemented IDs or assume today's snapshot remains fresh.

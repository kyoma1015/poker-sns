# B | TDA authentication guidance regression
Date: 2026-10-20 JST
Status: CONDITIONAL PASS; browser QA pending.

Base main: f8890b6ec11d30676c55dc7dc8801f1da8549d28; PR #6/#7 already merged and not reapplied.
Bug: getUser transport/503 errors previously sent users to login as if sessions expired; thrown requests could escape the action.
checkQuizAuthentication now separates verified login expiry from transport failures and returns retry guidance on unavailable auth services. No scoring/RPC grants/question content changes.
Tests: node tests/tda-quiz-auth.test.mjs: 11 PASS, covering guests, verified users, transport errors, explicit expiry and thrown errors. All dependencies mocked; no live authentication.
Locked install/build/lint cannot run locally because registry proxy is unavailable; PR CI verifies those gates.
Question-level official-rule validation BLOCKED: no complete source question bank/official text bundle accessible in this checkout. Historical 350/1400 counts are not remeasured. No historical SQL rerun.
Remaining: authenticated/expired-session browser QA and independent official-rule/duplicate-question audit. Published question correctness UNKNOWN.


## Integrated verification update (2026-10-20)
Integrated in B → D → A → SNS order. Local network permission resolved the previous registry blocker. npm ci, full unit regression, build and lint now run successfully on the integrated source; see INTEGRATION_VERIFICATION_20261020.md and docs/qa/integration-20261020/. Earlier blocked statements above describe the previous lane task. No production DB verification or release approval is implied.

## Continuous batch B (2026-10-20)
Branch codex/b-tda-quality-continuous-20261020, based on integrated PR13 SHA3ca87764e988cac588fef915d48823702a1a3326.
Implemented structural question validation, caught filter/fetch/answer/detail transport exceptions with no automatic answer retry, and offline count/duplicate-candidate audit CLI. The optional explanation request cannot discard an already saved answer on a thrown exception.
Added17 unit tests (full106 PASS) and real Chromium mocked mobile390x844 QA5 PASS. npm ci/build/lint PASS (48 existing lint warnings). Evidence/commands: docs/qa/b-tda-continuous-20261020/RESULT.md and logs.
Published350/official逐条/answer correctness remain UNKNOWN: no complete export or official source bundle was received and no live DB access was made. CLI never authorizes publication. No question content, SQL, permissions, main or production modified.

## Issue22 B — audit CLI boundary fix
New branch codex/b-issue22-audit-20261020, base PR14 4e16f7a7b567237d2735f1392906a6b1de2b7c23. Fixed parser-error source-fragment leakage and strict positional/count argument validation. Fixed reason codes never echo input text, read paths or raw error details. Added18 CLI tests; full124 unit/build/lint PASS. Evidence docs/qa/b-issue22-audit-20261020/RESULT.md. No official350/逐条 source received, no publication/DB/main/production operations. Empty no-count export false-pass remains a separately bounded next task, not silently declared fixed.


## Historical PR19 isolated release evidence (retained, not current status)
# B | TDA isolated main-based candidate
2026-10-20 JST. Branch codex/b-tda-rpc-isolated-release-20261020, base main f8890b6ec11d30676c55dc7dc8801f1da8549d28.
TDA question payload validation, caught RPC transport errors and offline count/duplicate-candidate audit implemented independently of unmerged PR13. Extra sources from PR13 were not imported. Main's existing inline auth logic is preserved; PR11's auth transport correction remains separate.
17 unit tests,5 mocked real mobile Chromium tests, locked install/build/lint PASS. Evidence and release limitations: docs/qa/b-tda-isolated-release-20261020/RESULT.md.
No live DB/auth/SQL or production operations. Published350/official-source comparison remains UNKNOWN; no question publication approved. Runtime RPC/auth integration and existing production high dependency issues remain release gates.

## Offline answer-key audit continuation — 2026-10-23 UTC
Stacked on PR98, source-only new module `src/tdaQuizAnswerAudit.ts` adds question/key join integrity, option membership, explanation/reference shape, four-choice counts and displayed answer-position histogram. Fixed19 acceptance:17FAIL/2PASS before ->19PASS after. Synthetic350/1400 fixture is explicitly not the published corpus; official accuracy remains UNVERIFIED and publication false. npmci/build/lint PASS; complete regression/CI evidence is in `docs/qa/b-answer-key-20261023/`. No existing parser/UI/RPC source changed. Official immutable snapshot and clause review remain BLOCKED.

## PR116 continuation — duplicate answer-conflict candidates (2026-10-23 UTC)
Offline audit now distinguishes same normalized prompt/option-set with contradictory answer meanings from harmless ID/order differences; only candidate IDs are returned, never an official correctness decision. Orphan duplicate key rows retain both referential findings. Fixed11FAIL->11PASS and inherited19PASS; UI/RPC/parser unchanged. Main and handoff full trees had no named complete350 export/official text candidate; scoped source-search evidence does not prove global absence. Official rule accuracy remains UNVERIFIED, publication false. Evidence:docs/qa/b-answer-conflict-20261023/.

## Interrupted snapshot-integrity work resumed — 2026-10-24 UTC
Preserved test input5ca250f/sourcecf130fd from the interrupted PR119 follow-up; clean before resume, no source reimplementation. Offline exact-byte hash/count/UTF8/structural audit CLI,26fixedFAIL->26PASS; source/test hash retained. Full resumed regression/build/lint and exact-headCI are recorded in docs/qa/b-snapshot-integrity-20261023/ and the follow-up Draft. Hash match is not provenance/official accuracy; official350/key/text/clause evidence remainsBLOCKED, publicationfalse. No UI/RPC/grading or retainedstate/production changes.

## Strict snapshot JSON —2026-10-24 batch
Continue saved ec826a8 branch without a new PR. Fixed snapshot ambiguity16tests14FAIL/2PASS→16PASS: duplicate decoded object keys (escaped alias too), nonfinite exponent and overdepth rejected with redacted existing reason codes; normal strings/distinct objects pass. New helper/scripts only, no UI/RPC/grading change. Existing26snapshot acceptance retained. Full local evidence docs/qa/b-json-ambiguity-20261024/. Official350/source/translation/clause-review remainsBLOCKED; concrete receipt contract there. No PR/CI activation or main/production/controller/state changes.

## Strict JSON exact-boundary QA —2026-10-24 continuation
Continued b00466d after exact GitHub HEAD verification. Added20 permanent tests, including deterministic10000-value valid JSON compatibility, depth127/128/129, malformedUTF8, duplicate decoded aliases, and generic reason/UNVERIFIED/no-publication invariants. All20PASS on existing source: no new source bug invented. Existing13 root testfiles unchanged; local build/lintPASS. Full regression and one environment-only sandbox retry are recorded in docs/qa/b-json-boundaries-20261024/. Official350/source/translation/逐条review remainsBLOCKED; no newPR/manualCI/production/retainedstate/controller operations.

## Legacy offline CLI strict parser inheritance —2026-10-24 continuation
Found a concrete uncopied repair: old scripts/tda-audit-cli.mjs still normalized duplicate JSON/overflow/invalidUTF8 while new snapshot CLI rejected them. Fixed input8tests6FAIL/2PASS→8PASS using existingstrict helper and rawbyte reads; genericINVALID_JSON/UNVERIFIED/publicationfalse maintained. No UI/RPC/grading change or duplicated parser. Evidence docs/qa/b-legacy-strict-json-20261024/. Official350 evidence remainsBLOCKED; no newPR/manualCI/heldstate/production operation.

## Real offline CLI process/file QA —2026-10-24 continuation
Added8 execution-boundary tests for actual old/snapshot CLI subprocesses and own temporary files: valid bytes, duplicateJSON, hash-matched invalidUTF8 and empty files. Generic reasons/channel/exitcode/UNVERIFIED/publicationfalse verified. All8PASS on existing repaired source; no invented source patch. Full evidence docs/qa/b-real-offline-entrypoints-20261024/. Official350 and逐条evidence remainBLOCKED. No PR/manualCI/production/heldstate changes.

## Quiz save recovery and completion —2026-10-25
Existing PR119 descendant now preserves an uncertain save without inviting duplicate writes and offers explicit unscored continuation/completion. Confirmed answers remain usable while optional explanation is pending; generation guards prevent stale reads from replacing a later question/run. Confirmed-answer count and original review numbering are preserved, unknown outcomes are neither wrong nor correct. Same final seven actual React synthetic-transport scenarios are compared on pristine245d55 and repaired source; existing six browser cases are retained. Actual locked Supabase SDK with injected fetch additionally confirms one POST each on503/network/permission rejection; no global SDK/API configuration changed. Exact tests/build/lint and limits: docs/qa/b-save-recovery-20261025/RESULT.md. This is client-flow implementation, not official350 accuracy, real DB idempotency, main integration or release. Official source evidence remainsBLOCKED.
Same-tick follow-up: actual React double option activation before render reproduced two submit RPCs (fixed8cases7PASS/1FAIL). A synchronous generation-scoped ref claim prevents duplicate dispatch while preserving permission/auth retries and confirmed/unknown retention. Source/test evidence and targeted final regression are in the same QA directory; full final-source CI remains separate.

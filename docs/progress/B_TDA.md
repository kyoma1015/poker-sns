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

## Latest search response boundary — 2026-10-21 23:05 UTC
PR62 be0fd9197bb17c0ff6de15ec9527a12ff49241c2 extends PR59 with optional rendered text/string collections/related-rule-number validation before state. Missing/null compatibility, latest-request gate, fixed error and retry retained. Fixedbrowser16 baseline10PASS6FAIL ->16PASS; unit138/npmci/build/lintPASS with existingwarnings;CI39690895245SUCCESS. Sourceonlysrc/TDA.tsx; protected4 files unchanged. Actual formal host agent after fresh36PR/strictGitproof/state/lease gates. No official question/scoring/SQL/production changes. Official350 accuracy remains unverified. Detailed evidence: PR38 docs/workers/SCHEDULED_CONTINUATION_20261022.md.

## Evidence audit — 2026-10-22
PR62 source unchanged and CI39690895245SUCCESS rechecked. The existing audit-cli-expected350.json is synthetic1question/count_mismatch, not350 reviewed questions. Complete official source bundle, immutable published350 export and all-question clause-review ledger were not found in inspected B checkout (GitHub-wide absence not proved). Need official version/URL/hash, full question-choice-answer-explanation-clause snapshot/hash, reviewer/date/dispositions/correction diffs and duplicate decisions; remeasure actual published count. No unresolved question gets new publication approval. Full checklist: PR38 ISSUE22_FOLLOWUP_20261022.md. No DB/corpus change.

## New source continuation — 2026-10-22
B83 sparse quiz/option validation: fixed23/saved14/audit18 +types/build/lint PASS, CI SUCCESS. Aggregate-rate candidate remains BLOCKED on original RPC spec. See [ledger](../workers/ISSUE22_AUTONOMOUS_SOURCE_20261022.md). Existing source/original4state/BLOCKED history retained; no production/main/paid action.

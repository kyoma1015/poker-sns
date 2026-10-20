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

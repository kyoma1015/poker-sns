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


# D | Diagnosis phase-one candidate
Date: 2026-10-20 JST
Status: CONDITIONAL PASS; release BLOCKED.

Base main: f8890b6ec11d30676c55dc7dc8801f1da8549d28.
Compared audit ac9a9fadec33373861d5f4436ed4cd6440634732 and QA d494b058a1d9cca62f5210a05f81a9f3584b5383.
Ported QA result URL/request invalidation/retry/question validation/normalized presentation and fixture tests. The audit-only avoidSkillGuarantees display corrections were missing from QA; ported all three replacements into a pure tested function used for loaded detail. Stored data is not mutated.
QA's newer advice thresholds and normalized rankings are preserved; audit's older 25-percent ranking filter is not imposed over the newer fixture expectations.
Acceptance: 50-question validation, 32 ceilings, 30 fixed personas, stale requests and display-only copy corrections.
Tests: node tests/player-type.test.mjs: 40 PASS (38 upstream plus 2 distinct wording regression cases). Fixture replay is not live QA or validation of all 36 classifications.
Dependency install/build/lint blocked locally by the same unavailable registry proxy; PR CI runs locked install/build/lint.
No scoring/animal definition SQL or L01 application. L01 current production state UNKNOWN; no DB read/write performed.
Remaining: current-SHA browser QA, PNG comparisons, result navigation/latency/failure recovery, classification semantic mismatches. PR #5 and A's diagnosis changes must not be blindly merged on top.


## Integrated verification update (2026-10-20)
Integrated in B → D → A → SNS order. Local network permission resolved the previous registry blocker. npm ci, full unit regression, build and lint now run successfully on the integrated source; see INTEGRATION_VERIFICATION_20261020.md and docs/qa/integration-20261020/. Earlier blocked statements above describe the previous lane task. No production DB verification or release approval is implied.

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

## Active continuous development — 2026-10-20
Base PR #13 @ 3ca87764e988cac588fef915d48823702a1a3326; independent D branch codex/d-diagnosis-quality-continuous-20261020.
Acceptance was recorded before source edits in D_CONTINUOUS_ACCEPTANCE_20261020.md.

Fixed an actual reproduced bug: opening a share editor for result A and navigating to owned result B retained A's caption/editor. Mobile Chromium baseline fails (expected no editor, actual one). Loading another result now clears result-specific drafts/messages/action state.
Also guard late save exceptions/finally and late share/image completions with the existing result-generation gate. Leaving a result prevents its asynchronous completion from adding messages or initiating a later PNG download on the current screen. A share write already submitted is not undone; this is stale UI protection, not server-side cancellation.
Moved the unchanged 36-animal display map to playerTypeAnimals.ts and added exact PNG inventory regression. No question text, option scores, classification definitions/thresholds or SQL changed.

New offline audit: `node scripts/audit-player-type.mjs` — 50 questions, 222 options, 32 score ceilings, 36 mapped animals/36 PNG assets and 30 persona fixtures; no structural errors or exact normalized duplicate question text. **CONDITIONAL PASS**, because the fixture does not include authoritative 36-animal classifier definitions/human labels. Semantic classification accuracy remains UNKNOWN, not improved by assertion.
Tests: `for test_file in tests/*.test.mjs; do node "$test_file" || exit; done` — 91 PASS (D42), `npm ci`, `npm run build`, `npm run lint` PASS (existing warnings remain).
`node tests/browser/diagnosis.mjs`: 6 PASS on Chromium 154.0.8037.57, viewport 390x844. Actual TSX with in-memory transport and external requests blocked: caption reset, stale share completion, non-owner action hiding, reload/PNG 1080x1500/no overflow, Q50 failure/retry exactly50 IDs, restart URL reset, and late save error isolation. This does not prove live authentication, RLS, DB isolation or actual Safari/mobile OS behavior.
Evidence: docs/qa/d-continuous-20261020/. CI additionally runs the audit and mobile diagnosis browser suite on PRs against the integration branch.

Release gate: Draft on top of PR #13. No main merge/deploy/DB/SQL/paid service operations performed. This D patch cannot make PR #13 release-ready; inherited notification/poll DB gates and dependency security issues remain. A main-based selective D release would require the prior D phase-one dependencies and independent QA, not a whole-PR13 merge.
Next: obtain the authoritative classifier definition and reviewed 36-animal labels for a semantic confusion audit; run isolated DB tests for saved/public/private result visibility and real auth sharing, plus Safari/PNG text visual comparison. Continue safe independent work without changing classification scoring by guess.

## Issue22 follow-up — offline score-row integrity
Base PR #18 @ 9051047cfe30bb2a38bb80c8985c0e7ad16e470c; branch codex/d-issue22-audit-20261020.
Reproduced a small real defect: appending an identical option score row to a temporary copy of the fixture still returned CONDITIONAL PASS/exit0. The audit built a Map first, silently losing duplicate evidence. The offline audit now checks duplicate and orphan option score IDs before aggregation and returns FAIL for either. Added an importable pure audit entry point so malformed copies can be tested without modifying the stored fixture.
Tests: new 5 regression cases (equal duplicates, corrupt overwritten duplicates, orphan rows, missing-score preservation, unchanged fixture/nonmutation), all unit96 PASS, npm ci/build/lint PASS. Ordinary historical fixture remains CONDITIONAL PASS with semantic classifier accuracy UNKNOWN. No application TSX, scores, classifier thresholds, SQL, DB or production changes.
Evidence: docs/qa/d-issue22-20261020/, acceptance: D_ISSUE22_ACCEPTANCE_20261020.md. CI target filter additionally supports the parent D branch for the stacked Draft PR.
Next bounded worker candidate: validate persona answer completeness and valid A–Z choice mapping in the offline audit only; empty persona answers currently remain CONDITIONAL PASS (next-worker-reproduction.json). Do not infer classification correctness or rewrite any fixture data.

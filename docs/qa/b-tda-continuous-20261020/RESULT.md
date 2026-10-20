# B TDA continuous development result — 2026-10-20 JST
Status: CONDITIONAL PASS for development; production release not performed.
Base: PR #13 integration 3ca87764e988cac588fef915d48823702a1a3326.
Branch: codex/b-tda-quality-continuous-20261020.

## Implemented
- The three question fetch modes validate actual RPC payload shape before storing/rendering. Invalid or duplicate IDs, missing/null options, blank text, duplicate option orders and noninteger order fail closed with retry guidance. Valid option order is sorted on a copy, without changing IDs or source records.
- Quiz filter/question/answer/detail requests catch thrown transport exceptions. Existing returned RPC errors still use their existing UI path. No automatic retry is added to answer writes (a failed transport does not prove that the write did not commit).
- An optional explanation request failure no longer loses the already saved answer or leaves the answer spinner stuck. Submission result remains the authority for correctness; neither answer keys nor scoring was changed.
- Added offline JSON export audit CLI with count check and normalized duplicate-question/choice candidates. It does not use a DB, publish questions, or establish TDA semantic correctness. Every report says official_rule_accuracy=UNVERIFIED and publication_approved=false.

## Actual verification
`npm ci --cache /workspace/work/npm-cache --fetch-retries=0 --fetch-timeout=15000`: PASS.
`for test_file in tests/*.test.mjs; do node "$test_file" || exit; done`: 106 PASS, 0 FAIL (existing89 + new17).
`npm run build`: PASS; existing Vite large-chunk warning.
`npm run lint`: PASS; existing48 warnings, no errors.
`node tests/browser/tda-quiz.mjs`: Chromium154.0.8037.57 / 390x844 viewport:5 PASS. Real TDA TSX with synthetic questions and an in-memory transport; external HTTP requests blocked, no real authentication or DB. Normal/hard/wrong request rejection recovery, malformed-options fail closed, saved answer survives optional-detail failure with one submission.
Offline CLI manually exercised with a synthetic one-question export: expected350 -> exit1 REVIEW_REQUIRED; expected1 -> exit0 STRUCTURE_PASS; missing arguments -> exit2. These are CLI tests, not a 350-question audit.
The CI workflow now accepts the integration target branch and runs the new browser suite as well as existing suites.

## Source inventory / blocked
The tracked baseline contains src/TDA.tsx, src/tdaQuizAuth.ts and api/tda-ai.ts, but no exported complete quiz bank or official TDA reference bundle. Question UI reads RPC-provided records; production DB was not connected to obtain them. Published350 is an owner-provided count, NOT remeasured here. The bank's answers/explanations/options and official逐条 coverage remain UNKNOWN, not PASS.
Run with an approved offline export:
`node scripts/audit-tda-questions.mjs /path/to/questions.json 350`
Expected input is a JSON array of question_id, question_text, difficulty/category (string|null), options [{id,option_order,option_text}]. Audit candidate duplicates manually; do not auto-delete or auto-change answers based on normalization. Correctness requires immutable question export, official TDA edition/source and a per-question human-reviewed evidence ledger, all still unavailable.

## Release / next work
No main merge, deployment, Supabase/SQL changes or publication. Branch is intentionally based on unmerged PR13; it must not be merged wholesale into main. UI/helper changes are TDA-only and could be cherry-picked after separate base-main reconciliation, security dependency gates and required isolated integration validation. A failed answer submission may have committed server-side: this patch deliberately does not introduce blind retry or a claim of exactly-once DB semantics.
Next independent B work: response-result structural validation and keyboard/focus QA; full content auditing waits for actual offline source evidence, not further speculative source claims.

# B Issue22 — offline audit CLI boundary fix
Executed: 2026-10-21 08:03 JST (2026-10-20 23:03 UTC). Status: CONDITIONAL PASS; no publication or deployment.
Base PR14: 4e16f7a7b567237d2735f1392906a6b1de2b7c23.
Branch: codex/b-issue22-audit-20261020. Existing PR14/19 read before work: neither already fixes the boundary.

## Actual defect and fix
`JSON.parse` exceptions may include a quoted source fragment. The old CLI echoed error.message, contradicting its own no-payload-log comment. A synthetic malformed export containing PRIVATE_DRAFT_ISSUE22_SENTINEL reproduced an input fragment in stderr (before.stderr.txt). No private question or user data was used.
The CLI now runs through a testable boundary that catches read, JSON and question-validation errors separately and emits stable INPUT_READ_FAILED / INVALID_JSON / INVALID_QUESTION_DATA reason codes. It never forwards raw error messages or file paths. after.stderr.txt records the same malformed input producing only INVALID_JSON.
Argument count is now exact (1–2 positional arguments). Invalid counts, surplus arguments and positive-integer overflow return usage exit2 before reading a file; Number.MAX_SAFE_INTEGER is accepted exactly. No rounded/Infinity count is accepted.
Valid output fields, count mismatch and duplicate-candidate behavior remain unchanged. Official accuracy is always UNVERIFIED and publication_approved=false. The runtime TDA UI, answer keys/scoring and source corpus are unchanged.

## Verification
- `npm ci --cache /workspace/work/npm-cache --fetch-retries=0 --fetch-timeout=15000`: PASS.
- `node tests/tda-audit-cli.test.mjs`:18 PASS, including three input-fragment cases, read-error redaction, malformed row data, argument cardinality/count boundaries, non-publication output and exact safe-integer limit.
- `for test_file in tests/*.test.mjs; do node "$test_file" || exit; done`:124 PASS (prior106 +18).
- `npm run build`:PASS, existing large-chunk warning.
- `npm run lint`:PASS,48 existing warnings, no errors.
- Actual executable with the synthetic malformed export returned exit1 and fixed INVALID_JSON on stderr, empty stdout. The new pure runner tests the same function called by the executable; no child-process-output mock substitutes for CLI logic.
- Browser code not changed. CI also retains existing mocked mobile browser suites; browser/runtime-DB coverage is not inferred from CLI tests.

## Boundaries and next task
No DB, network question source, public corpus publication, correct-answer change, main merge or production operation. Published350 count and official逐条 correctness are still UNKNOWN because the underlying export/reference corpus was not received.
Independent next defect is recorded in next-task-reproduction.json: an empty array with no expected-count still reports STRUCTURE_PASS, despite having no questions to audit. Do not fix runtime parseQuizQuestions([]), which correctly allows an empty RPC result; fix only offline report verdict. A bounded worker task descriptor is provided to the coordinator for that next step.

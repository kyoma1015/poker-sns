# B TDA continuous batch acceptance — 2026-10-20
Base: PR13 integration HEAD 3ca87764e988cac588fef915d48823702a1a3326.
Changes limited to TDA UI/helper, offline audit CLI/tests and B progress. Shared Timeline/DB/scoring untouched.
Before edits, observed: quiz fetch casts untrusted RPC data, then UI calls options.map; rejected RPC throws leave loading set. The answer-detail RPC can throw after a saved answer and leave the submit spinner stuck.
Acceptance:
1. Malformed question/option payloads fail closed before rendering; no answer key/scoring modifications.
2. All three fetch modes recover from thrown/returned failures; retry remains possible.
3. Optional explanation failure cannot lose a successfully saved answer or trigger automatic re-submission.
4. Offline question export audit detects structural errors, duplicate IDs and normalized text/choice duplicate candidates; does not call data verified or publish anything.
5. Unit tests, build, lint and mocked real Chromium QA pass with zero live DB calls.
6. Full published-350/official-rule correctness remains UNKNOWN unless exact exported questions and official references are actually recovered.

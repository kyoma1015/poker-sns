# B legacy offline CLI inheritance repair —2026-10-24 UTC

Start local/GitHub branch HEAD1056dc61d9eae80a0624880cf3049107c677b4ab, branch codex/b-snapshot-integrity-audit-20261023. Existing strict snapshot parser QA is retained, not reimplemented. Review found scripts/tda-audit-cli.mjs still used JSON.parse independently. Same ambiguous/invalid input rejected by the strict snapshot entry point could pass the old offline audit entry point.

Fixed input b6a1175: tests/tda-legacy-strict-json.test.mjs8tests, 6FAIL/2PASS before ->8PASS after. Six hashless legacy inputs: duplicate question text, escaped duplicate questionid, duplicate optionid, ignored metadata exponent overflow, overdepth metadata, malformedUTF8 in question text. Before repair all six returned code0/STRUCTURE_PASS, silently normalizing contradictory or invalid input. After repair all code1/INVALID_JSON, official_rule_accuracyUNVERIFIED, publication_approvedfalse; no source fragments escape.

Minimal repair scripts/tda-audit-cli.mjs:3 imports existing parseUnambiguousJSON; default local read preserves bytes instead of replacing invalidUTF8 during string decoding; parser invokes helper, retaining injected string-I/O compatibility. No new parser implementation or UI/RPC/grading change. Existing reason codes unchanged. This CLI is offline only; official accuracy cannot be inferred.

Commands: node tests/tda-legacy-strict-json.test.mjs before/after; all tests/*.test.mjs directly with Node24 and CHROMIUM_PATH=/usr/bin/chromium; npm run build; npm run lint; git diff --check. Exact logs and regression-summary.json alongside this report. Chromium scenarios use synthetic mocked transport, no live auth/DB. All existing tests are preserved.

No new official350 snapshot/key/original/translation/per-clause reviewer evidence received in this lane. Original material accuracy remainsBLOCKED. Candidate global optionID uniqueness was investigated but deliberately not implemented: authoritative TDA schema contract unavailable here; no new specification inferred.

No newPR/manualCI/main/production/retainedSQLite/job/lease/reservation/controller/host/billing changes. Same existing branch receives normal commit/push only. Next: obtain approved immutable source bundles under ../b-json-ambiguity-20261024/SOURCE_RECEIPT_REQUIREMENTS.md, then run offline byte/hash/structure and separately perform official clause review. Existing depth scan is after JSON.parse, not a hard allocation/time guarantee; legacy CLI still lacks a separately specified file-size limit.

Final measured result:15suites265PASS/0FAIL (inherited257+new8); no retry required. Build/lint exit0, inherited chunk/lint warnings retained. All14 inherited root testfiles byte-identical to1056dc6; protected.json retains SHA256s.

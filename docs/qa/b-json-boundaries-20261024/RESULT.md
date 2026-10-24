# B strict JSON boundary continuation (2026-10-24 UTC)

Start local and GitHub branch HEAD: b00466ddb494a37c82aa74568697ff4745410c1f.
Branch: codex/b-snapshot-integrity-audit-20261023, stacked on saved PR119 follow-up.

Added 20 permanent acceptance tests, including one fixed-seed (0x544441) 10,000-value finite JSON compatibility test. Duplicate decoded prototype/empty/emoji/backslash aliases, exact accepted depth127/128 and rejected129, malformed UTF8, grammar, escaped finite scalar values, and CLI generic reasons/UNVERIFIED/publicationfalse are covered. Input bytes must remain unchanged. All20 passed before any source edit: no new defect was proven and no source patch was invented. The previous16 ambiguity and26 snapshot tests are unchanged.

Commands: `node tests/tda-strict-json-boundary.test.mjs`; each `tests/*.test.mjs` executed directly using Node24; `npm run build`; `npm run lint`; `git diff --check`.
Initial full regression attempted257 tests:240PASS/17FAIL, in2suites only. Failures are sandbox `listen EPERM 127.0.0.1` and nested browser `spawnSync EPERM`; exact output is retained in regression.txt. Those two suites receive one retry with explicitly enabled network and CHROMIUM_PATH=/usr/bin/chromium; see retry.txt/retry-summary.json. This is environment classification, not weakened assertions. Build and lint exit0, existing lint/chunk warnings retained. protected.json proves all13 inherited root test files unchanged from the starting HEAD.

No new official350 snapshot, answer key, original edition/translation or per-clause expert evidence was supplied to this lane. Official accuracy remains BLOCKED/UNVERIFIED; hash/structure success cannot authorize publication. Receipt requirements remain ../b-json-ambiguity-20261024/SOURCE_RECEIPT_REQUIREMENTS.md. No production/network DB/auth or public question validation occurred. Generated10,000 values are synthetic parser compatibility tests, not350 official questions.

No new PR, manual CI, main merge, production, held SQLite/job/lease/reservation, host/controller or billing changes. Existing workflow runs tests/*.test.mjs automatically if a separately authorized PR later triggers it; this batch does not activate it.

Next: receive immutable official question/key/source/translation/reviewer evidence under existing receipt contract; execute offline CLI on approved local originals; retain clause accuracy BLOCKED until actual review. Resource bound remains accepted5MiB buffer and depth128; JSON.parse runs before depth scan, so this is not a hard memory/time limit.

Retry completed: tda-quiz-data28/28PASS and worker-acceptance16/16PASS, zeroFAIL, actual Chromium with synthetic mocked transport. Combined final result257/257PASS (prior237+new20). No live production/browser authentication claim. Initial17 environment failures remain recorded rather than overwritten.

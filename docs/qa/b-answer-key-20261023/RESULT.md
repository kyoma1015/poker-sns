# B — offline answer-key audit (2026-10-23 UTC)

CONDITIONAL PASS. This is a new offline sidecar audit API, not a change to public quiz answer retrieval, scoring, RPC grants or question publication.

Base: PR98 `8b1e0cf79160135bf69711abe69a2dffb8701a09`; stacked Draft only. PR14/23/28/32/41/59/62/83/98 validation, search, error recovery and filter changes remain inherited; no existing source is modified or reapplied. Scope is the new `src/tdaQuizAnswerAudit.ts` module and its tests/CI/evidence.

Fixed test-only input commit `3790b4f` contains 19 acceptance cases: before implementation 17 FAIL / 2 PASS (the two existing malformed-data assertions already throw when the feature is absent); after implementation 19 PASS / 0 FAIL. This is a missing feature baseline, not a claim of a production scoring bug. Acceptance file is unchanged by implementation.

The function accepts existing question-export structure plus a separate offline answer-key array: `{question_id, correct_option_id, explanation, rule_numbers}`. It detects missing/orphan/duplicate keys, answers outside the option set, missing explanation, malformed/duplicate positive integer rule references, non-four-choice questions and empty corpus. Existing normalized duplicate candidates are reused. Answer positions are measured after established option sorting, without mutating input. Counts/distribution are measurements; no invented fairness threshold or official semantic judgement is imposed.

`node tests/tda-answer-key-audit.test.mjs`:19 PASS.
`npm ci --cache /workspace/work/npm-cache --ignore-scripts`:PASS.
`npm run build`:PASS (existing bundle-size warning).
`npm run lint`:PASS (existing repository warnings).
A default-sandbox full regression attempt failed at a protected browser child-process spawn (EPERM); unchanged tests were then rerun with the authorized shell execution profile. The initial failure log is retained rather than relabeled PASS. CI runs all existing tests with Chrome and no database credentials.

`synthetic350.json` is generated synthetic data only:350 questions/1400 options; correct displayed positions 88/88/87/87. It is NOT a received export of published questions, and rule number1 in its synthetic keys is not a rule-correctness assertion. A complete immutable published350 snapshot, official text/version/hash and per-question reviewer evidence are still BLOCKED. `official_rule_accuracy=UNVERIFIED` and `publication_approved=false` hold even for STRUCTURE_PASS.

No live Supabase, SQL, production, scheduler, controller switch, retained SQLite mutation, main merge or paid services. Browser regressions use in-memory synthetic transport. Remaining: run this audit against an owner-provided immutable question/key snapshot, then perform official clause-by-clause semantic review; never commit private source exports without explicit authorization.

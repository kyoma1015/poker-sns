# B — duplicate answer-conflict candidate audit

2026-10-23 UTC, CONDITIONAL PASS. Stacked on PR116 `fedfa620a440f0abf92417e00d90687d3cdb0464`; old19 tests and existing parser/UI/RPC source are unchanged.

Fixed test-only input `329d537`:11 tests / 11 FAIL. Source `abcfa3d` makes11 PASS / 0 FAIL; PR116's19 acceptance remain19 PASS. New test SHA256 `ad71d4cc2a0ccd170cfa85c25f5ae8e3b7b6e3182e96b3827e20193d045a5264`; PR116 test hash remains `e1ae634fb242138321cfd8d6f45f08ff0f1f8e1ee28fc369d2fd5783e6b4b9fb`.

Same normalized prompt and same normalized option-text set with differing correct-option meanings produces `duplicateAnswerConflictCandidates`. Different option IDs or display order alone are not conflicts. Changed prompt/option set, invalid/missing/duplicate answer keys and ambiguous duplicate option texts cannot invent a definite conflict. Candidates include only question/option IDs, not full private prompt/explanation text. Existing duplicate-option reports remain. Orphan duplicate key rows retain both ORPHAN and DUPLICATE diagnostics.

Normalization matches the existing NFKC/whitespace/case duplicate-candidate policy. These are manual-review candidates only; hidden scenario context and official semantic correctness are not inferred. Nothing changes quiz answer selection, RPCs, published content or official answers. Even STRUCTURE_PASS always has official_rule_accuracy=UNVERIFIED and publication_approved=false.

GitHub main and handoff-branch recursive trees were read with truncated=false. Their path candidates did not include a complete immutable350-question export or official rule bundle; scoped evidence is in source-search.json. This does not prove global absence, inspect private storage, or convert synthetic data into originals. Official350/1400 accuracy, original source hashes and clause-by-clause review remain BLOCKED pending actual source artifacts.

Tests: node tests/tda-answer-conflict-audit.test.mjs; node tests/tda-answer-key-audit.test.mjs; all tests/*.test.mjs individually; npmci/build/lint. Full final results and CI are recorded in the Draft PR metadata. Browser transport is synthetic and external requests are blocked. No live auth/DB integration is claimed.

No production Supabase, retained SQLite/job/lease changes, scheduler/controller activation, main merge, Vercel operations, paid service or question publication. Next: use received immutable question/key snapshots and official review evidence; further heuristic candidates must remain review-only until confirmed.

Observed local results: npmci PASS; full regression195 PASS / 0 FAIL (11 new +184 inherited), npm run build PASS, npm run lint PASS with existing repository warnings. The full regression includes synthetic mobile browser scenarios; it does not use live production accounts. `git diff --check` PASS. Fixed11 test and PR116 test SHA256 match their immutable inputs.

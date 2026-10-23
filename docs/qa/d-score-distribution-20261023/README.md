# D offline score-boundary and distribution audit — 2026-10-23

PR100 source d89347092cfeb22b4ab8bc88e042f502df9d7798 is reused exactly as base. The source snapshot contains 50 questions, 222 options, 32 score dimensions and 30 historical personas, with 36 display animals/assets. It does not contain authoritative classifier definitions/thresholds or expert labels. No production data is retrieved.

New acceptance input 2a95e97: five tests fail because this quality audit did not expose score-boundary/distribution evidence. This is a missing audit feature, not proof that production diagnosis itself misclassified users. The initial five tests pass; the persona expectation additionally compares exact source-derived totals independently. An additional aggregate-overflow fixture reproduces 1 FAIL/6 at intermediate source 1c198f1 despite finite individual weights; after fail-closed aggregate validation, 6/6 pass. Existing 53 player-type cases and 5 audit cases remain unchanged and pass.

The offline audit now computes independently attainable per-axis minima/maxima, unique answer score-vector counts for every question, 1,000 complete seeded uniform answer profiles, score means/population variances/extrema and exact totals for the 30 historical personas. Seed 0x504944 is fixed. The source fixture is never mutated. Invalid source scores suppress the distribution instead of manufacturing evidence.

The fixed snapshot has no question whose options all have the same 32-axis vector. Selected exact reachable raw-score bounds: exploit -3..48; balance_awareness -3..19; deception -3..10; initiative 0..19. These are independent axis extrema, not a claim that all maxima are jointly attainable. Random sampling is a synthetic stress fixture and must not be used to infer real-player frequencies. A random sample not reaching an extreme is not evidence that the extreme is unreachable.

BLOCKED: 36-animal reachability, classification frequencies, semantic validity and expert persona alignment require the authoritative classifier/thresholds/tie-breaking version and human-reviewed labels. No animal labels or strategic correctness are invented. Existing advice copy/scoring/animal definitions/DB/UI are unchanged. Live Auth/save/resume/share/mobile E2E are not exercised here.

No main merge, retained SQLite/job/lease write, controller adoption, scheduler activation, production DB access, deploy, paid service or poll release. This is isolated development with a Draft PR stacked on PR100.

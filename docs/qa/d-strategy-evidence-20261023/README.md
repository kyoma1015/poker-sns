# D strategy-review evidence pack — 2026-10-23

Base PR118 f07b65135f43f413c41c9b124e37062d20e5197a. Existing PR114/118 CI is successful; this follow-up adds an offline review tool, not scoring/UI/schema changes. No existing fixes or protected tests are reapplied or altered.

Fixed6 new acceptance cases initiallyFAIL because traceable strategy-review evidence is missing. New source generates all50 question references,222 canonical option IDs, and196 varying question/axis score-contrast rows. Each row holds the exact first-option baseline and signed differences for other options. Tests independently reconstruct source weights across all50questions/32axes. It also indexes the eight exact literal review terms requested by the owner against question and option text, with separate question-match flags and matched option orders.

Current historical snapshot: ブラフ occurs in question/option text for questions40/42/43; ハンド appears in18 questions. ポラライズ,レンジ,強い相手,弱い相手,バランス,エクスプロイト have zero literal matches. This is lexical evidence only: absence does not prove conceptual absence, presence does not prove strategic correctness. No guessed mapping from words to axes/animals is introduced. The report explicitly leaves semantic validity BLOCKED and classifier NOT EXECUTED even when additional terms are inserted in a test fixture.

All960 historical persona references remain matched;50/222/32 and36 display assets remain intact. Corrupt score/reference input suppresses the strategy pack instead of publishing apparently valid evidence. Source fixture and existing tests remain unchanged. New6PASS, existing53+5+6+14PASS =84PASS; npm ci had completed before interruption. On resume, build and lint succeed locally with prior warnings retained; the configured isolated CI is pending observation.

No new authoritative classifier/threshold/tie-break table or expert label artifact has been supplied. Prior bounded discovery evidence remains docs/qa/d-persona-reference-20261023/README.md; the same tree/ZIP searches are not repeated. Actual36-animal reachability, classifier boundaries, distribution and meaning remainBLOCKED. Historical raw-score consistency and synthetic QA do not establish classification validity.

CI preserves the full generated JSON as a seven-day d-strategy-review-evidence artifact; summary.json is a bounded source snapshot. No production DB/Auth/UI interaction, retainedstate writes, job/lease/reservation creation, controller adoption, paid service or main merge. Independent launchUNKNOWN; unattended operationOFF; pollNO-GO.

## Usage-limit recovery — 2026-10-24
Recovered the unchanged source work and existing baseline/regression logs from commit9cc2fe3 and its uncommitted working tree. Re-ran only the new six-case acceptance after source review; reused the prior78 regression results locally, with full84 configured in independent CI. All eight inherited fixture/test/application files are byte-identical to PR118. No classifier data arrived; prior BLOCKED gates remain.

# Feature completion and integration readiness — 2026-10-26

This ledger distinguishes the user's completion classes from development lanes.

| Completion class | Work | Current gate |
|---|---|---|
| A: can advance by implementation | Notification read/realtime/retry, TDA account scope, diagnosis result/share lifecycle, bounded GTO report consumer | Implemented and locally exercised; match exact published HEAD to automatic CI |
| B: can advance by integration/verification | Selected SNS/quiz/diagnosis sources on current main; consumer CLI | Isolated main-based composition with main package/lock preserved; no main merge/release approval implied |
| C: needs external evidence/permission | Authentic DM schema/RLS/DB auth/idempotency; TDA350 originals/key/reviewer; formal classifier/thresholds/ties/expert labels | Missing artifacts/isolated environment; remain BLOCKED, not replaced by synthetic success |
| D: substantial development | Full 2–9-player/20-stack GTO, full EV/convergence/G9/G11 historical compatibility, stores/dealer/preflop full contracts | Partial engine/tools are not final-scope completion. Preserve all original requirements |

## Reconciliation evidence

All77 open PR metadata/changed files and fixed base/head SHAs are saved in docs/qa/integration-readiness-20261026/open-pr-snapshot.json; target-ancestry.json records actual ancestor heads. `git merge-tree --write-tree main head` only writes local Git objects, not branches or files. At the initial snapshot main781f038415503ece850c25a26e72ef67dee9c8a1:

- PR119 base is B answer-key branch, PR120 base is C training branch, PR121 base is A host-boundary branch; none targets main. Their whole histories conflict with current main in old SNS/poll/MASTER files.
- Shared conflicts include Timeline.tsx, TimelineInteractive.tsx, interactiveRequests.ts, poll-only test/browser and progress files. Selecting a newer header or filename alone cannot resolve semantic overlap.
- PR124 has no initial textual merge conflicts, but targets its D persona-reference base rather than main. Clean Git merge does not prove backend privacy, classifier validity or approval.
- PR122 tags and PR123 video remain separate owners; App/Timeline/PostDetail/video SQL/workflows are not edited by this batch. Poll release/backup/diagnosis-v2 DB are excluded.

No existing PR base was changed and no whole old branch was merged. Proposed feature-only order: B quiz parser/auth/UI closure, D question/presentation/result closure, A DM/notification UI closure, then independent C offline consumer/native closure. No runtime/controller adoption in this sequence. Existing deployment/release gates apply separately. The main-based candidate deliberately preserves main's package/lock (including its differing undici override); dependency/security integration remains a separate reviewed scope, not silently imported from an old branch.

## Main-based candidate

A temporary checkout at /workspace/work/issue22-main-feature-candidate-20261026 overlays explicit files only; composition.json records each source blob and source checkout/head. Local commands/results are preserved at /workspace/work/issue22-main-feature-evidence-20261026/. The candidate is intentionally unmerged and is not a new remote branch/PR. Retain its uncommitted overlay for review, not production use. Selected-file compilation/browser QA cannot prove that an entire old Draft PR can be merged safely.

The GTO consumer accepts the real native proof through its stdin CLI in that main-based candidate, matches the producer's checked view and static HTML, and keeps unknown frequencies/EV visibly unavailable. No app router connection or real-poker equilibrium claim.

## Release gates and restart

No direct PR119/120/121 whole-branch main merge is ready. PR124's textual integration is possible but still needs scope/review/auth/privacy approval. The selected feature-only composition is a local integration candidate; real DB gates/physical-device QA and explicit main approval remain. CI success is never release authorization.

Refresh exact public HEAD/CI and other-owner diffs before applying any candidate. Read held SQLite mode=ro, compare original4/all45/run1-limit28/checkpoint. No held jobs/leases/oldBLOCKED mutations. AUTO-RESUME OFF, independent startup UNKNOWN, poll publication NO-GO. Source/test/publication details live in each existing Draft PR and lane QA; do not replay completed tasks or extend schedules.

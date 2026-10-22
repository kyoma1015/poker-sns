# Issue22 safe continuation verification — 2026-10-22 UTC

Overall **CONDITIONAL PASS**: two formal-host source tasks completed, tested, committed and published as separate Draft PRs. Production release remains **NO-GO**. This explicit-user invocation is not an independently scheduled cold-start or a daemon test. No scheduler changes, main merges, Vercel operations, production DB access or paid services were performed.

## Evidence ledger

| Item | Verdict | Measured evidence / limitation |
| --- | --- | --- |
| PR66 fixed-input source and CI | PASS | b492f8c7730cb5ebb66beee909ba2526dcb7cc85; fixed29 + existingGTO40; Actions39711822875 success. Original v1 descriptor remains BLOCKED, not rewritten. |
| PR66 whole inherited branch vs current main | FAIL | Non-destructive `git merge-tree --write-tree --name-only MAIN HEAD` exits1, seven conflicts. API compare diverged, ahead22/behind113,120 files. Input-base mergeability does not establish main mergeability. |
| B official source identity | PASS | Official rules page heading observed: 2026 Rules, Version1.1, Sept21,2026. Full raw Longform PDF/RP/Addendum not recovered; rendered webpage is not an immutable original. |
| B full published350 / per-clause accuracy | BLOCKED | No complete immutable question snapshot/hash or ID-level review ledger in inspected artifacts. Existing expected350 report contains one synthetic question, not350 reviewed questions. Accuracy UNKNOWN; no new publication. |
| B audit tooling | PASS | `node tests/tda-audit-cli.test.mjs`:18/18. PR62 existing source retained; no duplicate implementation. |
| D structural consistency/regression | PASS | Audit50 questions/222 options/32 dimensions/36 display keys/36 distinct genuine PNGs; audit tests5 and classifier tests42 PASS. |
| D36 semantic classification | BLOCKED | Thirty synthetic persona expectations are trait descriptions, not animal labels: zero authoritative animal-labelled cases. Authoritative classifier thresholds/tiebreaks/expert labels missing; no semantic-validity claim. |
| SQLite initialization root cause / isolated fix | PASS | Deterministic pre-fix27 tests:2FAIL. WAL/schema connection setup bypassed existing cross-process setup guard; failure leaked connection. Draft69 serializes initialization with existing bounded guard and closes failed connection. Fixed27, worker22, queue15 PASS; CI39718156506 success. |
| Live controller adoption of SQLite fix | BLOCKED | Draft69 is not merged/applied to existing controller or main. Isolated successful fix does not prove all future live startups safe. |
| Existing reconstructed GTO native execution | PASS (bounded) | Three separate modules/processes:960 synthetic one-iteration poker smoke cases; 17 settlement +16rank7 native-reference comparisons. Source hashes verified; originals unchanged; temporary checkpoints only. |
| Exact toy best-response measurement | PASS | Draft70 adds only gto/convergence.py. Fixed36 (7 errors before implementation), existingGTO40, nine saved policy replays within1e-12 PASS; CI39718705059 success. |
| Original G11 ABI/checkpoint compatibility | BLOCKED | Reconstructed pinned dependencies are not original G11 vendor/ABI proof. Original vendor manifest, reference settings/outputs and complete historical checkpoint not recovered in visible workspace. |
| Actual poker strategy convergence | BLOCKED | No approved game-specific BR/exploitability evaluator, owner20stack/bet fixtures, acceptance tolerance or multi-seed trajectories. Matching-pennies synthetic metrics are not poker convergence proof. |
| Poll production release | BLOCKED / NO-GO | Real private backup and isolated restore, approved operational/auth/privacy/cron release gates remain incomplete. No production connection attempted. |

## Branches, commits and CI

- Observed main: `4a5129143e26697b172eb08afc05d52d0d15e201`, including externally merged PR68. External main changes were read, not performed by this worker.
- PR66 base `115adb8a6ec7aff591aaf90d479a1eb205c1d24b`, head `b492f8c7730cb5ebb66beee909ba2526dcb7cc85`.
- Draft [PR69](https://github.com/kyoma1015/poker-sns/pull/69): `codex/a-sqlite-init-fix-20261022`, head `4d30c7ac0d08104f9d159987e38c823ef7c3b419`; fixed input `0ce21f5885b8a5a0c5e20fe5befdf626d910b4ca`; source only `scripts/code_worker.py`. [CI39718156506](https://github.com/kyoma1015/poker-sns/actions/runs/39718156506).
- Draft [PR70](https://github.com/kyoma1015/poker-sns/pull/70): `codex/c-convergence-metric-fix-20261022`, head `8ed4e56ddaee8a57141de108f41d2915d326aabe`; fixed input `3eb08c4723ec3ef55faf0b86f6b54768c1cab738`; source only `gto/convergence.py`. [CI39718705059](https://github.com/kyoma1015/poker-sns/actions/runs/39718705059).
- B PR62 `be0fd9197bb17c0ff6de15ec9527a12ff49241c2` and D PR60 `93d9948f8f829432fa66c5aafd294bf8924421fa` preserved. No second implementation or unsolicited integration.

PR66-main conflicts: docs/progress/MASTER.md, docs/progress/SNS_INTERACTIVE.md, src/Timeline.tsx, src/TimelineInteractive.tsx, src/interactiveRequests.ts, tests/browser/poll-only.mjs, tests/poll-only.test.mjs. Only merge-tree objects were created: no index/worktree/ref integration or conflict resolution was applied. Main source extraction/integration must be separately reviewed; do not merge this inherited branch wholesale.

## Host execution and source integrity

Original four task spec hashes match the retained manifest and remain implemented. Same durable state retained; no replacement SQLite. Each new task used a fresh complete open-PR snapshot, immutable input, protected FAIL baseline, exact allowed paths, dependency and overlap proof, then prepare/formal agent/trusted finish. Public sanitized plans/results are retained under `docs/qa/issue22-verification-20261022/`. Private receipt/token/state/credentials are excluded.

A: parent-held setup guard deterministically blocks child initialization; eight fresh initializers preserve all rows; injected schema failure releases guard/closes connection. Existing setup-lock bounds unchanged. AST review confirms all code outside initializer and setup-lock docstring unchanged. This fixes the reproduced race, not an assertion that every possible SQLite lock is impossible. Previous PR38 CI39712373480 attempt1 lock FAIL / attempt2 SUCCESS remains historical, not erased.

C: input policies must be two probabilities, exact int/float excluding bool, finite/in-range, normalized within absolute1e-12; no silent normalization/input mutation. Computes exact synthetic two-action zero-sum utilities/BR/NashConv/half-gap. Both proof flags remain false. No solver/checkpoint rewrite or dependency installation.

Native toy seed17/epsilon0.6: all three variants match NashConv at200=0.019921993558225992,2000=0.04879930218327844,20000=0.02749104685424275. Nonmonotonic finite trajectory; not evidence of full strategic convergence. Reconstructed Python3.12 and pybind11/Abseil pins pass local smoke but do not recover original G11 baseline.

## Next safe work and completion conditions

1. Review Draft69 deployment/adoption separately before changing live controller. Add fresh long-running contention evidence only if it tests a new failure mode; do not rerun completed task IDs.
2. Prepare GTO-only main integration input with exact inheritance/overlap evidence and protected tests; no main merge is authorized. Main conflict repair must preserve current poll-only/security changes.
3. B: recover immutable full published-question export and original official Longform/RP/Addendum bytes/hash using authorized read-only sources. Then question-ID clause-by-clause reviewer ledger; unresolved items cannot be approved for publication. Japanese v1.0/Englishv1.1 parity remains UNKNOWN. UI VERIFIED badge backend guarantee remains UNKNOWN, not a proven violation.
4. D: obtain authoritative36-class definitions/thresholds/tiebreaks plus independent expert animal labels; only then boundary tests/confusion matrix/image-description review can establish semantic coverage. Auth/save/public sharing QA remains separate.
5. G11: recover original dependency/ABI manifest, seed/config/reference results and complete checkpoint read-only. Run compatibility only on copies. Need a rule decision for dead-ante edge with no positive_live eligible seat; do not silently change eligibility to all_live.
6. Poker convergence: approved fixed game fixtures + independent BR metric/tolerance and multi-seed trajectory. Draft70 is a reusable toy validator, not this acceptance criterion.

No fresh executable next descriptor is asserted without independently measured FAIL tests and review. Existing completed A/C inputs remain immutable history. Remaining artifact/expert evidence limitations are not converted into PASS. Finite reservation untouched; no independent startup/daemon claim.

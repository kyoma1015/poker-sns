# Issue22 explicit-user continuation — 2026-10-22

Status: CONDITIONAL PASS. This run was triggered by the explicit user instruction,
not a scheduler. Do not add it to scheduled/cold-start proof. No scheduler dates,
count, credentials, production DB, Vercel deployment, billing or main were changed.

## C: correct the immutable specification before claiming success

Original4 jobs still match the retained manifest spec_hash values. The existing
SQLite was retained; no replacement was created. v1 input
`7fa1ffd5de8a7bb0479f4f5348445782326cde8e` reproduced fixed28/30subtest failures;
protected5 hashes and fresh37PR source ancestry passed the planner.

The coordinator's prior v1 descriptor was wrong: it called refund a scalar.
The formal agent followed that contract, but fixed28 failed with5 errors because
all17 valid fixtures contain refund vectors. Hash-verified preserved Betting.settle
initializes `refund=[0]*self.n` and returns that vector. v1 is **BLOCKED**, no
successful commit. Its descriptor, protected tests and failed source worktree
remain intact; do not rewrite v1 or report its original28 as passing.

One corrective retry used a new versioned ID `issue22-c-chip-oracle-types-v2`,
new input `115adb8a6ec7aff591aaf90d479a1eb205c1d24b`, branch
`codex/c-chip-oracle-v2-input-20261022`. New tests require refund/vector correctness,
add invalid scalar values for vectors and a valid partial-refund-vector control.
Before source dispatch, fixed29 had47 subtest failures; protected5 hashes and fresh
complete37PR/lease/dependency/strict Gitproof gates were revalidated. The new ID
does not modify the old immutable job or weaken the original safety controller.

Actual formal collaboration then wrote only `gto/native/settlement.py`:
rake must have exact int type, refund/net/pot_amounts/pot_rakes must be lists of
exact ints. bool/float are rejected before loading reference/native. Negative net,
partial expected fields, valid17 and actual equality comparisons remain supported.
No original fixture/reference/solver/checkpoint bytes changed.

Host finish verified fixed29/sourcehash/tamper/noop/commit:
`b492f8c7730cb5ebb66beee909ba2526dcb7cc85` on
`codex/c-chip-oracle-v2-fix-20261022`, Draft PR66.
Fixed29 PASS, existingGTO40 PASS, git diff --check PASS.
CI39711822875 SUCCESS. Original v1 remains BLOCKED; v2 is implemented.
No additional retry was performed. This does not prove G11 compatibility,
strategic precision, convergence or historical checkpoint resumability.

## B: maintain PR62, do not approve unreviewed questions

PR62 source `be0fd9197bb17c0ff6de15ec9527a12ff49241c2` and
CI39690895245 SUCCESS were confirmed. No B source was changed.
Existing `audit-cli-expected350.json` is a synthetic **one-question** count
mismatch (question_count1/count_matches=false), not a 350-question review.
The CLI keeps official_rule_accuracy=UNVERIFIED and publication_approved=false.

The inspected B checkout has no independently verified complete official bundle,
published350 export or full per-question review ledger. This is a scoped finding,
not proof that no such file exists anywhere on GitHub. Required evidence:

- Official URL/version/effective date/acquisition date and original-text hash.
- Immutable snapshot/hash containing all questions, choices, answer, explanation,
  reference clauses, IDs and publication states; remeasure the actual count.
- ID-to-clause review with scene assumptions, answer/choice/explanation reasoning,
  reviewer/date, dispositions, approved correction diffs and duplicate decisions.
- Resolve all reviewed-publication blockers; do not automatically delete duplicate
  candidates or publish unresolved questions. Auth/real DB/mobile QA is separate.

## D: regression coverage is not semantic validation

PR60 source `93d9948f8f829432fa66c5aafd294bf8924421fa` and
CI39640376299 SUCCESS were confirmed. No D source was changed.
Offline `node scripts/audit-player-type.mjs` returns CONDITIONAL PASS:
50questions/222options/32dimensions/36displaykeys/36PNG/30personas.
It explicitly reports classificationSemanticValidity UNKNOWN and live schema
NOT CHECKED. The30 personas are not expert-labeled coverage of all36 animals.

Needed: versioned classification definitions/thresholds/tie priority, names/
descriptions/images for every animal, expert-reviewed expected labels, boundary
examples/confusion matrix and reproducible fixtures. DB save/privacy/Auth tests
remain a separate gate. Do not revise classification meaning on regression alone.

## A and integration: main changes are not production release

PR64 merged as `c85cbff0dd543b39ef0effed9191f690dbfa0efe`.
CI39708426732 SUCCESS, job119593799325 log SUMMARY PASS56/FAIL0/BLOCKED0.
Its SQL now refuses a running poll/interactive command in cron.job_run_details
even after cron.job was unscheduled. The guard test seeds an isolated running
history row; this is not a production maintenance/drain rehearsal by this worker.

During this run, external PR65 also merged as
`3ff2c03bddcf74c252f2533769f79ccc85dba1fe`, whose first parent is PR64's merge.
It changes emergency disable helper ACLs and isolated tests, not C source;
CI39711407028 SUCCESS. Neither merge was performed by this worker.

All37 existing Draft PR base/head/file snapshots and recent Actions were reviewed:
31 clean,2 unstable,4 dirty against their **declared** bases at observation time.
PR13/12/8/2 conflict with main. PR59/60 Actions succeed but Vercel status fails
with deployment rate limiting; no deployment retry/403 workaround was attempted.
For35 heads, recent Actions include success; PR36/2 have no run evidence from
the queried head endpoint. This is UNKNOWN, not a passing CI verdict.
Internal-base clean status does not prove compatibility with latest main or
authorize release. Review successor/ancestor relationships; do not wholesale
merge PR13 or reapply old poll SQL over PR64/65. PR66 is a new independent draft
against its immutable input, not a main-integrated feature.

Poll release remains **NO-GO**. Actual private backup/export and full isolated
restoration are incomplete; the user's Mac is unavailable. Wait for a trusted
alternative execution environment, private storage/credentials handling and
authorized restoration checks. Do not put real exports/secrets in GitHub/CI/chat.
GoTrue/authenticated flow, cron maintenance/single-worker proof, rollback/ACL and
release authorization remain gates. No production was connected in this run.

Detailed snapshots, CI references, baseline/results and log hashes:
`docs/qa/issue22-followup-20261022/`. Private token/receipt/SQLite files are excluded.

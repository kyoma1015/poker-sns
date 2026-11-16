# PR120: release specification proposal and native qualification boundary

Start: cdb85e03508de8eed2fc1a4e5f28241eb007ed75, branch
codex/c-native-hand169-bridge-20261023, open/Draft. Read-only GitHub observations
in baseline-ci.json: all seven families / nine runs SUCCESS, attempt1. No manual
rerun. Prior candidate, certificate, integrity and search implementation reused;
no repeat recovery/ZIP/spec-history investigation and no source-data regeneration.

## A: concrete owner decision, not an invented original

../../specs/GTO_PREFLOP_RELEASE_PROPOSAL_20261117.md is approval proposal v1.
proposal.json binds its exact SHA256; A/B/C remain PENDING_APPROVAL. Prior original
source evidence is reused from ../preflop-release-20261116/spec-provenance.json.
The existing20-stack and full-sizing requirements stay intact. Numerical proposal
values have not become formal profiles. Equal vs unequal stacks, ICM/profile
mapping, seven rake profiles and house rules need the explicit recorded decision.

Recommended20 BB values:2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200.
Sizing proposal: all legal integer-chip raise-to targets,1BB=2chips. The document
also gives0.25BB and sparse-training alternatives, reasons and action-cap/UI/data
impacts. Current64-action transport limit cannot represent HU50's99legal root
actions. Do not truncate. Exact extension depends on owner size decision.
Accuracy numbers0.05BB player gain /0.05BB EV halfwidth /99.9% family confidence
are new proposed release policy, not recovered historical acceptance thresholds.

## B: fixed native-game probe and rejected totalizations

PROTOCOL.md was written before measurement. Existing two models, complete14196
preflop values, coarse learned flop teacher and native State/rules are reused.
Original candidates alone do not define all real-game histories; policy.py gives
a separately identified TOTAL evaluation-only extension: round flop wagers up to
legal chips, merge aliases by a public canonical child, unknown history fold if
facing or check otherwise, turn/river check/fold. Flop teacher tables are oriented
to the original caller's hero seat, not always SB. Policy observations accept only
own hole cards and visible public board/history. New digest includes completion,
source/model/rules. Evidence must NEVER be attached to the unmodified old digest.

Uniform full52-card worlds, all streets and all native sizes. Vsopen sampling is
weighted by source SB open reach with card removal, not uniform opponent class or
visit counts. Feasible deviations are SB3BB open and BB10BB3bet vs2.5BBopen.
Neither uses hidden cards; both are missing from source preflop abstraction.
Both deviation payoffs are fixed after opponent's explicit unknown-history fold:
SB+1BB / BB+2.5BB. Their vulnerability is a **counterexample to this completion**,
not evidence about any unimplemented richer completion or the frozen baseline.

| Model/context | Baseline EV BB (hero) | Legal deviation gain BB | Simultaneous interval BB | Root gain lower BB |
|---|---:|---:|---|---:|
| small/RFI |0.106689453|0.893310547|[0.204084443,1.582536651]|0.204084443|
| small/vsopen |-0.294982910|2.794982910|[2.039732576,3.550233245]|1.070249391|
| large/RFI |-0.035247803|1.035247803|[0.311262151,1.759233455]|0.311262151|
| large/vsopen |-0.421264648|2.921264648|[2.117572602,3.724956695]|1.170644192|

Each report16384accepted worlds,65536total,131072paired-arm rollouts,18.889626s.
First256worlds in each of four reports, both arms:2048native/reference replay
comparisons including legal sets, actors, ledger transitions, independent Python
vs C++ rank order and terminal net. Additional384test rollouts pass. This is a
finite replay check, not exhaustive equivalence proof. Rank acceleration for other
worlds reuses original C++ rank; Python betting remains separate. Pybind headers
are existing SHA-pinned free dependency; no paid service or external compute.

Bounded empirical Bernstein intervals use per-metric failure .001/(4*342), union
bound at least99.9% family confidence under IID simulation assumptions. SHA-based
public-keyed random tapes provide independent behavioral draws; PRNG simulation
and floating arithmetic are not rigorous roundoff proof. No best-seed selection.
All169strata are reported; every-report all169EV precision is insufficient.

Native-vs-model realized terminal cashflow difference was measured on the same
paths (means small/RFI0.000091553BB, small/vsopen-0.000584920BB, large both0).
This detects execution/rounding discrepancy only. It is NOT a uniform continuation
error bound over arbitrary deviations, and is NOT external GTO comparison.
Full independent BR UPPER bound, full-native NashConv, uniform model error upper
and omitted-action gain upper remain UNKNOWN. Lower bounds already refute the
proposed0.05BB limit for these totalizations. All four remain BLOCKED_UNVERIFIED.

No training or checkpoint changes. Frozen restricted-game population NashConv
0.9321071527220774BB is prior evidence, not remeasured. Same-game improvement
this task UNKNOWN; no subtraction of different-game metrics. Bad totalizations
not adopted. Original8candidates/1352rows stay BLOCKED; ordinary verified formal
RFI/vsopen strategies0. Existing HU1BB calibration is separate and unchanged.

## C: criterion-level completion work

acceptance-workgraph.json retains both original12-item checklists and gives each
criterion a concrete implementation/data/verification task, dependencies and
blocker. Whole formal PASS0/12→0/12, delta0;10PARTIAL/2BLOCKED. FAIL in its verdict
field means completion demonstrably unfinished, not preserved regression failure.
UNKNOWN #8/#11 means formal numerical specification still pending. No partial
transport/UI or subset quality measurement was relabelled formal PASS.

Existing src/GtoPreflop.tsx, preflopHistory.ts, rangeCatalog.ts, release generator,
review certificates, registry, frozen sources, pure BR, matched-history R/S and
static demo are unchanged. Search can still display opt-in research/legacy
calibration in their explicit scopes; formal RFI/3bet/4bet cannot be offered yet.
No new mobile/browser QA is claimed because no UI was edited; earlier QA reused.

## Reproduce / resume

```
python -B -m gto.qualification.build --directory /workspace/native-qualification-build
QUALIFICATION_BUILD=/workspace/native-qualification-build python -B -m unittest gto.qualification.test_qualification -v
python -B -m gto.release.verify_evidence
node --test --test-isolation=none tests/gto-release.test.mjs
```

Those locally PASS:10Python,8Node, old release integrity. New CI compiles original
thin native replay and runs the bounded regressions/frozen receipt checks; it does
not repeat the completed65536world measurement or old successful workflows by
manual dispatch. No changed TS/React/app package, so full npm ci/build/lint not
repeated locally this task; normal applicable CI still runs on the new commit.

results.json includes all169EV summaries, policy/source/build identities and
limits. results.checkpoint.json preserves last batch RNG/moments/completed earlier
reports. This is a progress checkpoint, NOT a solver R/S or supported automatic
resume loader. Completed results.json supersedes it; no automatic restart is
available. A new planned experiment must use a fresh output path and fixed budget.
Preflight2GiB disk reserve, measured128world runtime probe,180s hard stop used.
Probe outputs/build/logs are local /workspace paths, not claimed remote backups.

Next implementation: define/legalize size-response policies on unseen public
histories in a new isolated policy, including opponent re-responses and all later
streets; use the fixed native probes before any broader learning. Default fold is
explicitly rejected. Need an independent full-native BR upper (or proved model+
omitted-action envelope) and per-class/action EV precision before sending EXACT
same policy/condition identity through the existing review certificate to registry.
Then verify actual search/browser retrieval. Owner A/B/C approval defines coverage;
it cannot repair quality failures, and does not authorize any production operation.

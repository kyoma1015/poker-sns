# Coupled HU50 continuation study — BLOCKED_UNVERIFIED

Baseline commit6a8afecd0755971fd495c7c63b1b87a715ec00cd, DraftPR120.
Goal is verified strategies, not research counts. Result: verifiedRFI0/3bet0,
formal acceptance0/12 unchanged. Neither new learned policy is admitted.
No formal20-stack/size/MTT-ring/ante-rake specification adopted.

## Cause and minimal solver change

Existing C++ CFR correctly optimizes a FIXED payoff kernel. Previously the kernel
used old-chart conditional ranges, then runtime recomputed continuation from the
NEW chart. It is a different continuation policy/game, so old-anchor sampled
NashConv.078552 was not the final strategy's convergence value. Previous same
8world diagnostic.744173 remains historical, not an independent fullnative NC.

Five independent oracle regressions: 2private types/7public nodes, including an
SB second decision with nontrivial own reach; Python regret/average updates
match C++ at1/2/7/100iterations; brute-force information-constrained pure BRs
match. Sparse physical-card enumeration matches joint blocker removal/mass and
normalization; scaling range by17 preserves probabilities/value. Actual preflop
Bayes/posterior matches action likelihoods with own-card/board exclusion. Fresh
epoch instances reconstruct changed ranges instead of reusing previous caches.
Tiny signaling counterexample shows changing posterior reverses the continuation
response even with correct fixed-game regret arithmetic. These finite tests
found no CFR/card-removal defect; they do not prove correctness of every game.

`coupled_preflop.py` reuses existing C++ CFR and full three-street rollout, refreshes
ranges between inner epochs, then relaxes behavior toward the new response with
alpha.25. This interpolation is NOT CFR time averaging and has no joint-game
convergence theorem. Inner100iterations retain fixed payoff; ranges are updated
between epochs, not secretly updated inside those100iterations. Current-range
train and fresh-heldout kernels measured after every update. All169frequency
rows for RFI/vsopen/vs3bet regenerated (and vs4bet), all native legal action ids
explicit in frequency-and-EV artifacts; omitted training sizes still zero and
unknown histories use protected exact-history fallback, not fold fill.

## Multiple-seed learning curves — method rejected

Four train worlds/four heldout worlds per seed, exact compatible physical pairs,
board importance C(52,5)/C(48,5), same coins across within-seed epochs. No hidden
opponent/future cards given to policy. Distinct board samples, not private pairs,
are statistical units. Cumulative inner updates0/100/200:

| seed | current-range train NC | current-range heldout NC |
|---|---|---|
|17119101|1.900659 →1.808152 →1.690195|1.983504 →2.306844 →2.789328|
|17119102|3.580521 →2.412298 →1.786725|1.462726 →1.978215 →2.642746|

Both heldout curves worsen while train improves: small-world overfitting/unstable
range response is an additional diagnosis, not proof of population NC increase.
Both stop after two updates; NO8world/200iteration escalation. Per-seed runtime
58.288717/71.574062seconds (<180), kernel receipts/epoch strategies saved.
Undamped first-target controls on same heldout worlds NC2.954381/4.775522;
relaxed first update2.306844/1.978215 is less unstable but still worse than baseline.
The two-seed gate fails. This is not fullnative BR/NC, and comparisons to historical
.744173 use different worlds; no population improvement/deterioration claim.

## Independent native holdout

`native.json` and checkpoint: fresh seed17119111, fixed256worlds/4096native paths,
family99.9% across20 intervals; identical decks/tapes, original native engine.
Two learned policies vs oldB and previous reoptimized policy; six unilateral
attacks per learned policy: SB3.5BB open, BB10.5BB3bet, BB riverjam, SB immediate
fold, SB2.5BB open, BB9BB3bet. See JSON for every EV, paired interval and digest.
No interval excludes0 for any paired EV improvement or deviation. Large finite
open-size point estimates are not a quality PASS or proven exploit.

Conditional EV intervals for all169x3contexts x3selected actions use4heldout
public-board importance samples, union across6potential learned policies/1521
actions. Bounded reference-kernel estimates, NOT independent full-native all-action
certificates. Maximum clipped true-EV interval width100BB, precisionFAIL; full
legal-action native precision UNKNOWN. Training/payoff/source/build hashes and
all policy digests are recorded; no old B model metrics relabelled as new results.

SB2.5BB attack selected from exploratory native pilot; fresh fixed4096 confirmation
seed17119112 stopped at180second cap, completed2373worlds, last complete durable
checkpoint2304worlds. INCOMPLETE: no fixed-n confidence conclusion. No sample-size
extension or learning escalation. Restore from checkpoint, never treat omitted
worlds as0; future continuation requires a fresh explicit compute budget. This
failed time estimate is not reported as completed4096 evaluation.

Fullnative BRupper/NCpoint/NCupper, uniform continuation/range-coupling error,
omitted-size error and fulllegal169/action precision UNKNOWN. Restricted BR point
estimates and physical payoff ranges are NOT substituted for these missing bounds.

## Tests / recovery / protection

90 qualification regressions PASS (5new). Exact suite is workflow's unittest
command; test names/results in tests.txt. Original frozen A/CFR, oldB, HU1BB,
2-9players, research8candidates and demo untouched. Existing source dependency
NumPy2.3.5 reused. Initial pilot rejected NumPy scalar card ids before any completed
world; corrected conversion to native Python integers. Superseded evaluation
receipts/source preserved: inherited parent metrics in raw-control metadata were
corrected to actual100-iteration target metrics; numeric native results must agree.
No production/app/UI files. Local npm/build/lint/browser QA not performed.

Every epoch/chart and completed kernel world is in compressed Git artifacts.
Manual restart: load desired epoch strategy with existing load_policy, wrap in
RangePolicy using matching range.so, then existing payoff/evaluate/candidate
functions. Verify source/build/digest before continuing. Native/checkpoint worlds
include exact action RNG tapes; incomplete confirmation has2304durable rows.
No automatic resume service, and inner CFR regret arrays are not serialized;
100iteration solves are short deterministic restarts, not claimed exact regret
checkpoint continuation. Old external ZIP/DB bytes outside workspace not recovered.

Next quality work: reject simple relaxed fixed-point method; prototype genuinely
joint preflop/continuation optimization in an independent exact small game with
correct public information sets and multiple future completions, then compare at
same budget before expansion. Require independent native improvement, fullsize/
BR/error/EVprecision gates before certificate/registry/search admission. Pending
formal specs stay PENDING and do not block authorized isolated HU50 development.

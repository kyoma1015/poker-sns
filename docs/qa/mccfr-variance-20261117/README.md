# PR120: exact infoset reuse and variance-reduction comparisons

2026-11-17 JST. Starting cd78b228d7cf8eb865ab8e1fcb0f785e411a0b56,
PR Open/Draft confirmed. Prior successfulCI not manually rerun. Immutable legacy
solver, evaluator and checkpoint are unchanged; source reused via explicit
validated migration. Five small ablation checkpoints retained, zero qualified.
No UI, registry, formal-spec or other-development-line edits.

## Diagnosis in four parts

`diagnosis.json` is computed from the real prior checkpoint, not a progress note.
1. Cards: 433 distinct own-card pairs across rows; root256 updates split over238
   actual card pairs. There are1326 combos; exact suit symmetry has169root orbits.
   All1326 root observations map to exactly169keys in regression, without merging
   ranks, positions, sizes, histories, flush structure or turn/river order.
2. Reach: distinct rows preflop709/flop230/turn66/river17,590public betting histories.
   The broad legal-size policy and full-board chance fragment downstream coverage.
   River rows are only1.66% of distinct visited rows, not river reach probability.
3. Key: raw own cards + public board + complete ledger preserve information but
   needlessly separate global suit relabelings (and unordered flop permutations).
   New canonical key minimizes own/public cards under all24global suit permutations;
   no opponent/future cards used. Histories/actors/actions/public amounts untouched.
4. Update:1040updates/1022rows =>18repeats,1.7308%. RootS mass proves256root
   updates/238keys =>18root repeats; nonroot repeated updates0. No evidence of R/S
   being reset. Regression forces the same real deal twice and observes SAME key,
   changed accumulated R and growing S for both legacy and extended solvers.
   Independent matched-history expected CF-vector AND average sums match for
   recursive CV and first-owner external sampling, not just one-step shapes.

## Implemented algorithms

`variance_mccfr.py`: exact suit-orbit pooling plus recursive known-fold control
variate. Legacy R/S are SUMMED only in exact isomorphic orbits. Pooling changes
an asymmetric source policy; it is a NEW policy, never tagged as unchanged.
For each sampled owner action: v_a=b_a+1[a=sample]*(child-b_a)/q_a; v=sum sigma*v_a;
regret receives inverse own-prefix sampling correction, average sums unchanged.
The baseline is own public committed chips on fold; native payoff equality tested.
No clipping, missing-fold fill, sampled-action pruning or surrogate payoff model.
A perfect known baseline has zero variance in the toy; exact-fold alone is NOT
universally beneficial. Its variance-increase counterexample is kept in tests.

`external_first.py`: enumerate ALL legal actions at FIRST traverser decision,
outcome sample below; policy frozen until entire batch completes. First-node q1,
average weight1/action_count, downstream importance factors retained. Independent
CF/average oracle proves the normalization; actual99-action batch freeze and
S-mass1 tested. Stop before drawing chance if remaining budget<99 (worst case),
so cheap sampled deals are not selectively accepted. No incomplete branch list.
This implements bounded external sampling, not recursive full-tree enumeration.

## Same-budget warm-start ablations

Source checkpoint is identical for each arm; suit pooling is explicitly different
initial policy. Same exploration, training seed, target2sec/max1024 terminal paths.
Checkpoints each32paired iterations (external each64leaves). Wall time checked
between atomic updates; one update/checkpoint may exceed2sec slightly. Actual
training0.992–2.075sec. Source migration/setup excluded from training clock.

| arm | paired iterations added / leaves | total rows | NEW-window updates / distinct | NEW-window repeats |
|---|---:|---:|---:|---:|
| raw-zero |416 /832|2533|1633 /1571|62 (3.7967%)|
| raw-foldCV |416 /832|2533|1632 /1570|62 (3.7990%)|
| orbit-zero |480 /960|2412|1972 /1624|348 (17.6471%)|
| orbit-foldCV |480 /960|2408|1976 /1625|351 (17.7632%)|
| orbit-external |7paired /954leaves,14batches|1820|920 /920|0 (0%)|

Totals include reused source rows; raw source1022rows vs orbit source905rows, so
row totals are not directly comparable key-space coverage. Revisit rates above
exclude visits that occurred only in the source; including warm-source hits:
raw-zero7.47%, orbit-foldCV23.94%, external0.54%. External combines within-batch
root updates once, not99fake revisits. Only7new root classes vs raw354 and
orbit-CV145, illustrating lost chance coverage under its rollout budget.

Frozen-strategy512-path gradient-variance diagnostics use identical policy/seed
within each CV pair. Relative trace sample variance CV/zero:
| seed | raw | orbit |
|---|---:|---:|
|17112026|1.228562|0.252817|
|17112027|0.836382|0.861290|
|17112028|0.969817|1.343943|
No consistent CV benefit; do not report the first seed's75% reduction alone.
Trace magnitudes cannot be compared across raw/orbit target policies as though
only the CV changed. Sparse inverse-probability updates have severe heavy tails.
These are empirical diagnostics, not variance bounds or convergence certificates.

## Same-policy all169/action EV and feasible-response holdouts

Three final policies measured (raw-zero, orbit-foldCV, orbit-external), each169x4
worldsx(99+93)actions =129792 rollouts. Same RNG/protocol as previous evaluator,
source3BB-open posterior includes exact card removal.2world fit class-only pure
response,2disjoint holdout. Each evaluation<=90s, actual25.84/24.97/24.41sec.
All169/action means, frequency samples, intervals and digest stored in compressed
receipts. Per-class frequency/actionEV covariance caveat from prior study remains.
Posterior changes with policy; conditional vs3BB comparisons also change range law,
and are not paired same-range causal estimates. Source suit pooling also changes
initial policy; observed point differences cannot be attributed solely to learning.

| policy | RFI EV mean and simultaneous interval BB | vs3BB conditional BB EV and interval |
|---|---|---|
| prior saved | -4.268624 [-17.532996,8.995747] |1.559057 [-11.705309,14.823423]|
| raw-zero same budget | -4.212574 [-17.476945,9.051797] |1.808061 [-11.456327,15.072449]|
| orbit-foldCV | -4.062229 [-17.326600,9.202142] |2.214597 [-11.064432,15.493625]|
| orbit-external | -4.232949 [-17.497320,9.031422] |1.060659 [-12.203669,14.324987]|

The RFI interval width26.528742BB is UNCHANGED at4world/class; orbit-CV vsopen
width26.558056BB is slightly wider. Union-bound Hoeffding at same n cannot infer
narrower widths from a reduced sampled-gradient variance; they measure different
uncertainties. All169 precision still fails. No statistically established EV gain.

Feasible class-only one-decision held-out gain (NOT full BR), BB:
- raw-zero: RFI0.868946 [-36.648361,38.386253]; vs3BB-0.385236 [-37.902590,37.132119].
- orbit-CV: RFI0.735323 [-36.781984,38.252630]; vs3BB-0.355368 [-37.914131,37.203395].
- external: RFI1.078066 [-36.439241,38.595373]; vs3BB1.733374 [-35.783810,39.250559].
All include0. Full optimized independentBR, fullBR upper, NashConv and its upper
remain UNKNOWN/null. NO100BB physical bound substituted. Historical limited-game
NashConv0.9321071527220774BB is untouched and not an improvement comparator.
No surrogate continuation model; uniform execution discrepancy and conditional
EV/model accuracy are unproved, not assumed0. No quality admission follows.

## Verification, persistence, and decision

10new focused testsPASS (0.274s): real repeated updates,169exact orbits/24suit
permutations, native fold baseline, recursive CV/external expected CF and average,
full99branch freeze/average normalization, checkpoint exact resume and migration.
Five saved policies each32native/reference paths,160paths total including3BB,
10BB3bet,SB responses and HU50 short all-in. Policy digest unchanged by evaluation.
Old QA/Node/app/build/browser tests not manually repeated; no TS/package changes.
New automaticCI includes these10 tests with existing21; observe result separately.

Local budget before compute7.2GiB free, total local compute budget5min, saved
compressed evidence1.2MiB (<20MiB). Short pilot/refactor reruns remained bounded;
all CV seeds/failed gates retained. No long training or automatic restart.
`comparison.json`,`variance-replicates.json`,`external-comparison.json` retain
measured costs, coverage, ratios. Five gzip checkpoints include source/RNG/iteration/
regret/average/origin;3gzip EV receipts bind checkpoint and implementation hashes.
`native-replay.json`,`diagnosis.json`,`python-tests.txt` are actual results.

Expansion gateFAIL: coverage reuse improves, but robust variance/EV/BR improvement
is unconfirmed. Do NOT expand any arm or register GTO. Formal0/12→0/12;
normal verified RFI0/3bet0;8legacy candidates1352rows remain BLOCKED_UNVERIFIED.
No formal20stack/size/rake/ante specification adopted. A/B/C remain PENDING.
Next: fit predictable baselines from independent revisits and validate on fresh
seeds; preserve exact information while improving chance/leaf allocation. Complete
response bounds still required; more iterations alone are not the next action.

Reproduce limited experiments (does not start an autonomous scheduler):
```
QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_variance_mccfr -v
python -B -m gto.qualification.variance_study --build /tmp/poker-public-response-build --source docs/qa/native-mccfr-20261117/checkpoint.json --output /tmp/new-variance-study
python -B -m gto.qualification.external_first --build /tmp/poker-public-response-build --source docs/qa/native-mccfr-20261117/checkpoint.json --output /tmp/new-external
python -B -m gto.qualification.variance_evaluate --build /tmp/poker-public-response-build --checkpoint docs/qa/mccfr-variance-20261117/orbit-external-checkpoint.json.gz --output /tmp/new-external-ev.json
```
Resume external with --resume <saved gzip checkpoint> and same source; batch parity
persists. VarianceSolver.restore loads other gzip states after gzip/JSON decoding,
with exact identity/RNG checks (tested). Do not overwrite saved evidence. Legacy
checkpoint still restores in unchanged legacy solver; no inaccessible-old-session
DB/ZIP is claimed recovered. Production/main/SSO/DB/Storage/Vercel/fees untouched.

## External RNG correction

Review found branch replay could leave the master RNG at an earlier consumed
position. Corrected by sampling a shared pre-owner prefix once, reserving a
branch seed from master, and using independent branch RNG objects (common seed
within the batch). Branch draws never rewind or advance the next-deal stream.
New regression proves master state unchanged when branch draw counts vary1→100.
Corrected external checkpoint, native replay and all169/action EV are the values
above. Old external artifacts remain accessible at276765ad075fb8b21fa7bbb0754a65538aacd8fe,
and are superseded. Other arms unchanged; their receipts explicitly pin that
historical source commit, preserving old source hashes rather than rewriting them.

## Native-only fold counterexample: stronger stop evidence

`probe_native_fold.py` uses ONLY NativeState observations/legal actions/returns,
not Python betting or surrogate continuation. Each frozen policy8192fresh iid
root worlds; master deals and policy-action streams separated. Total24576native
paths,1.530/2.010/2.826seconds, all completed. Source95faa0c and checkpoint hashes
are pinned in `native-fold-probe.json`. No policy update during measurement.

| policy | native root SB EV interval BB | exact legal fold gain interval BB | complete BR gain / NashConv LOWER bound BB |
|---|---|---|---:|
|raw-zero|[-6.785676,-2.177092]|[1.677092,6.285676]|1.677092|
|orbit-CV|[-5.868440,-1.259856]|[0.759856,5.368440]|0.759856|
|orbit-external corrected|[-6.626497,-2.017912]|[1.517912,6.126497]|1.517912|

Three simultaneous99.9% intervals (fixed-n Hoeffding). SB-fold payoff is exactly
-0.5BB at HU50 root, independent of own/opponent cards. Any complete BR is at
least this feasible deviation; zero-sum NashConv=sum of nonnegative unilateral
gains is at least the SB gain. All three evaluated strategies are refuted by
this deviation. No conclusion is drawn for the two unevaluated ablation arms.
The lower bounds are NOT optimized BR/NashConv point estimates or upper bounds,
and their ordering does not prove convergence improvement. All upper/point
fields remain null. Legacy limited-game0.932107BB remains a different scope.

Root profile interval width4.608584BB is narrower than previous26.528742BB
because this probe spends8192samples on root EV, not4perclass/allactions. It is
a different allocation/estimator, NOT evidence that solver variance or all169
precision improved. This gives a concrete stop reason rather than replacing
unmeasured fullBR by100BB. No broad learning/registry promotion follows.

```
PYTHONPATH=. python -B docs/qa/mccfr-variance-20261117/probe_native_fold.py --build /tmp/poker-public-response-build --folder /tmp/copy-of-saved-variance-folder
```
The folder must contain the3saved gzip checkpoints; use a copy to preserve Git
evidence. Runtime guard30s/policy, incomplete fixed-n runs do not claim confidence.

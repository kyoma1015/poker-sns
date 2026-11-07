# Extended legal-response games and probability-stratified population EV

Research only. No real-poker GTO guarantee. External comparison NOT PERFORMED;
real-game approximation error UNKNOWN; formal acceptance remains 0/12.
Frozen preflop CFR, research eight ranges/1,352 rows and static demo are unchanged.

## Registered experiment

`protocol.json` was committed before training. Excludes all 177 earlier board
suit orbits from new 14 training, seven validation and seven final boards.
Only validation selects the cheapest of 512/2048/8192 simultaneous CFR sweeps.
`selection-lock.json` records selection bytes before the once-only final test.
CI is deterministic reproduction, never another model-selection opportunity.
Population samples are separately registered, may include known boards, and are
not used for candidate selection or labelled new unseen tests.

## What the action expansion changes

Previous four/five **complete-plan arms** tie responses together. The new trees
let each player's private abstraction choose a behavioral action separately at
each public betting history. First model uses half-pot bets; second allows
1/3, 1/2, 3/4 pot bets in the same game. Bet amounts are capped at remaining
stack, duplicates removed, calls match contributions, and one 3x raise is legal
when chips remain. Under-minimum raises are all-in only. Call/fold follows that
raise. Turn and river check through. This is not the complete NLHE action tree.

Input to decisions is that player's own abstract private type and public
history; no actual opponent hole card. Chance is a **joint**, card-removal-aware
private-type distribution, not independently multiplied marginals. Exact
conditional flop showdown moments integrate all compatible hole-card pairs and
990 turn/river runouts. Private features remain coarse and do not recover
within-bucket information available to a real player.

The standalone C++ engine propagates opponent realization reach for each
counterfactual regret update, and own realization reach for average strategies.
Best response sums opponent types before maximizing by own type at its public
information set. The resulting BR sandwich and NashConv concern this restricted
zero-sum game. The positive cumulative counterfactual regret certificate bounds
average-strategy NashConv; it does not bound omitted NLHE actions or abstraction
error. Legacy mixed plans are converted to behavioral probabilities conditional
on that player's own preceding choices. Naively averaging plans at every history
would break equivalence; independent ledger/profile and exhaustive BR tests cover
this distinction. Half-to-multi off-tree extension is declared in the protocol,
not presented as a unique or theoretically optimal extension.

## Full-population integration and unevaluated regions

The actual frozen preflop history followed by CALL determines board chance via
all legal hole-card combinations and card removal. Its 22,100 physical boards
are partitioned into eight texture strata, including trips. Within each stratum,
pre-fixed IID-with-replacement draws use those **actual probabilities**. Allocations
32/64/128 per stage depend only on known stratum mass. Repeated boards retain
sample multiplicity, but count only once toward exact probability coverage.

For population inference each board uses a separately specified **uniform-init
512-sweep** full-multi solver. This deterministic board-to-profile algorithm is
not the selected warm-initialized final-test profile. Even when it has not
converged, independent exact BRs sandwich that board's restricted-game value.
Check/fold guarantees both players at least -pot/2, so game value lies within
[-pot/2,+pot/2]. Any profile lies in [-50,+50] BB for the HU50BB ledger.

For weights W_s and sample sizes n_s, weighted Hoeffding radius is
`range * sqrt(log(1/delta) * sum(W_s^2/n_s) / 2)`. There are 2 stages × 3
checkpoints × 4 one-sided confidence tails; delta=0.01/24 yields simultaneous
99% family coverage under the registered IID-PRNG sampling assumption. This
bounds population-integration sampling error, not game-model error. The local
BR width remains separate. Deterministic bounds assign safe extreme values to
all unevaluated probability mass. Statistical, deterministic, analytic and
previous-checkpoint intervals are intersected; an empty intersection is a
recorded failure, never a reason to redraw seeds or conceal data.

`evaluated_board_probability` is actual numerically evaluated physical support.
A statistical interval about all boards does not mean 100% computed coverage.
Global equilibrium here permits the public flop to determine the restricted
game; it is not an equilibrium of the frozen preflop strategy or of full poker.

## Reproduction and safe restart

Run from repository root, system Python and C++17 only, no new paid service:

```
python -B -m unittest tests.test_street_coverage -v
python -B -m gto.abstract.street_study --phase select --build-dir /tmp/street-select --output /tmp/street-selection.json
python -B -m gto.abstract.verify_export --actual /tmp/street-selection.json --expected docs/qa/street-coverage-20261105/selection.json
python -B -m gto.abstract.street_study --phase final --build-dir /tmp/street-final --output /tmp/street-final.json
python -B -m gto.abstract.street_study --phase population --build-dir /tmp/street-pop --cache-dir /tmp/street-cache --output /tmp/street-population.json
```

Final evaluation validates source, protocol, frozen predictor and locked selection.
Population rows are atomic, checksum- and identity-guarded; restart reuses complete
rows without zero-imputing missing work. In this session the durable cache is
`/workspace/gto-street-population-cache`. No independent auto-restart exists.
Next unseen study must exclude `next_unseen_excluded_orbits`, including boards
seen during population integration. Preserve failures and never select anew on
this final set.

`external-reference-spec.json` records public-source availability and exact
matching requirements. Code availability is not a matching reference solution,
and code licensing does not establish permission to redistribute numerical data.

## Root bookkeeping extension

`street_root_bounds.py` is a post-registration, read-only bookkeeping extension;
it does not fit or select policies or access any additional unseen boards.
It independently traverses the frozen 169-class preflop strategy, conserves
terminal probability mass, sums fold payoffs exactly, applies the two conditional
**uniform512 profile** EV intervals with correct SB/BB signs and CALL-prefix
probabilities, and bounds all other CALL continuations by ±50BB. Their payoff is
not assumed zero and not assumed to match the original frozen engine. Thus the
reported root interval is a set of possible EVs for fixed preflop actions with
these two new research continuations and all remaining continuations unknown.
It is not the original full frozen-policy EV, a preflop best response, or GTO.
`computed_root_board_probability` multiplies conditional physical-board coverage
by actual prefix probability. This is smaller than conditional flop coverage.

Local BR calculations enumerate finite expectations without Monte Carlo noise,
but use floating point. The 1e-7BB numerical guard and independent ledger tests
are not a formal interval-arithmetic rounding proof. Neither sampling bounds nor
local convergence control omitted-action, private-abstraction or real-game error.

## Observed results

Validation selected 2,048 sweeps. Final cohort: seven new boards × two public
prefixes × two frozen initializations × two games = 56 contexts, all NC <0.1BB.
They are not 56 independent physical preflop configurations.

| Evaluation game | Final mean / worst NashConv BB | Legacy4 in same game | Legacy5 in same game |
|---|---:|---:|---:|
| Half pot, independent public-history responses | 0.022473 / 0.039353 | 2.772126 / 7.499834 | 0.732482 / 2.450938 |
| Three simultaneous sizes, independent responses | 0.047962 / 0.087937 | 4.828094 / 11.991729 | 2.471998 / 4.160916 |

The learned half-only profile extended to multi has NC mean1.848614/worst3.860065BB.
Thus convergence in the smaller game does not certify the expanded one.
Normal-form/behavioral profile lift maximum EV discrepancy:1.421085e-14BB.

| Population target | vs3bet | vs4bet |
|---|---:|---:|
| Unique physical boards computed |128|128|
| Actual conditional chance coverage |0.584523%|0.586923%|
| Restricted game value simultaneous99% interval BB |[-5.435229,1.112933]|[-15.920299,-0.810468]|
| Fixed uniform512 profile EV estimate BB |-2.164317|-8.374738|
| That profile's simultaneous99% interval BB |[-19.946027,15.617394]|[-26.154138,9.404661]|
| Sampled mean local BR bracket width BB |0.146746|0.175135|
| Unevaluated profile contribution deterministic bound BB |±49.707739|±49.706539|

All registered population criteria passed; none establishes real-poker GTO.
The profile statistical intervals are much narrower than their deterministic
missing-mass bounds, **under the sampling assumptions**. These population
profiles/games differ from the previous study; this is not a paired EV-accuracy
comparison of one frozen policy. Actual root computed chance is only0.015370%,
other CALL continuations retain56.253315% mass, and the root EV set is still
[-28.687245,28.500945]BB. No complete preflop EV precision claim follows.

Local tests:57 preserved +16 new =73 distinct PASS. Research CI performs these
and regenerates selection, final, population and root attribution. Final-head CI
is pending at the results commit; the PR and external receipt record its actual
conclusion. Formal0/12, new normal GTO ranges0, existing research8/1352 unchanged.
New unseen experiments must exclude410 recorded suit orbits, not merely177.

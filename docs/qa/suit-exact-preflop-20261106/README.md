# Full finite-population payoff oracle → coherent preflop learning → research UI

This removes counterfactual oracle sampling uncertainty in one explicit HU50BB
condition. It does NOT certify ordinary real-game GTO. Formal0/12 is unchanged.

## What is enumerated

The same two learned flop controllers, their own/public information abstraction,
all9matched preflop branches and the preflop betting tree are fixed. For each
physical flop, all compatible concrete hole pairs and990turn/river runouts define
an affine fixed-policy payoff. Simultaneous global suit permutations preserve169
private classes,card removal,own flags,public texture,position/pot/SPR/history and
class-based reach. All22100flops partition into1755orbits. We multiply each
representative contribution by its physical orbit multiplicity,not equal weights.
Prior registered physical representatives are reused deterministically,not chosen
by value/cache presence. Full169²conditional board mass sums to1(error0at output
precision). This reduction is not valid for arbitrary suit-dependent policies or
ranges; do not extend it silently. Actual8texture permutation tests passed with
max perboard payoff disagreement4.337e-19BB. Allin same-class diagonal residual
9.860e-19BB. Input/source/design frozen before integration. No new unseen-test
claim; this is the complete finite population for a pinned model.

## Separate evaluation integration from learning

The previous sampled policies were recovered from their actual pre-evaluation
freeze and checked against the published joint digest. Same-policy/same-controller
comparison now gives:

|model|previous simultaneous MC NashConv interval BB|same policy,enumerated numeric-guard interval BB|new policy trained on exact tensor BB|
|---|---|---|---|
|small|[0,7.711587009]|[0.021715158742,0.021715338002]|[0.001505467301,0.001505651561]|
|large|[0,11.665099038]|[0.022569531025,0.022569697595]|[0.001422508028,0.001422675688]|

Independent Python private-information BR integrates opponent classes before
maximizing per own class/history. It matches native evaluation to7.574e-15BB.
Pure-policy exhaustive tests and a perfect-information counterexample validate
that hidden opponent cards are not used by the response. These BRs allow all
preflop decisions while keeping flop profiles fixed,NOT all poker deviations.

New rootSB EV small[0.030880211883,0.030880305006],large
[0.037254171989,0.037254255296]BB,net before blinds. All four contexts have169rows
per model,three actionEVs/mixed frequencies per row. Largest actionEV numeric
interval width2.000000397e-7BB (previous MC widths up to37.94BB).

Sampling error is0for this finite fixed-controller integration. Displayed new
intervals propagate empirical1e-7BB leaf numerical guards; they are NOT99%CI,
NOT a formal floating-point rounding proof,NOT real-game error bounds. The two
models still differ: mean perhand frequencyTV RFI0.117487,vsopen0.170394,
vs3bet0.108210,vs4bet0.119797; maximum actionEV differences0.543265/2.123463/
3.896475/7.647099BB respectively. This is model sensitivity,not external GTO error.
Continuation information/action abstraction,teacher training distribution and
postflop policy optimality remain unvalidated for actual poker.

## Artifacts, UI and reproduction

protocol/design/source commit0456999preceded full integration; a1175c3 froze
same-policy baseline/comparison and UI semantics before final results. The older
independent-preflop20261105 snapshots remain unchanged. results.json retains all
policies/contexts/quality/numeric audits with exact SHA/count fingerprints for
three binary packets. Complete arrays are preserved locally at
/workspace/suit-exact-full-results.json; cache /workspace/independent-oracle-cache.
CI regenerates actual packets and validates checksums and exact numeric
fingerprints; no missing array is zero-filled. Normal float comparisons use1e-12.

Existing GTO search presents the new8ranges1352rows only after explicit research
opt-in and exact HU50/noante/norake/2.5/9/21/50 conditions. v2 distinguishes
finite enumeration/numeric guards from v1 statistical intervals; ordinaryGTO
catalog admission remains rejected even though both computed research NC targets
are met. Old8ranges1352,H U1BB,2..9regressions,staticdemo/frozenCFR remain protected.

Use new GTO finite-population preflop precision workflow for exact commands:
source/manifest→5tests→design replay→finite cache prefill+enumeration→CFR→independent
BR→all output replay→same-policy comparison→reference adapter. No old successful
CI is manually rerun. Reference acquired0,comparison0/676per model,external
accuracyUNKNOWN. See ACCEPTANCE.md for the twelve retained release requirements
and remaining source/model/condition blockers. No production/main/SSO/fee changes.

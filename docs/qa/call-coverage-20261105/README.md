# High-reach matched CALL continuation evaluation

Research only: external GTO NOT PERFORMED, real-game approximation error UNKNOWN,
formal acceptance0/12. Frozen preflop CFR, eight research ranges/1352 rows, HU1BB,
2–9-player regressions and static demo unchanged.

## Registered scope and information

Protocol and source/design were committed locally before their computations.
Local freeze ledger records dates; later GitHub API commit creation is not an
external trusted preregistration timestamp. No final-set model selection.

Exact public prefixes from HU50BB/rake0/ante0 pinned tree:

|Prefix|Root probability|Hero for continuation EV|Pot BB|Remaining BB|SPR|
|---|---:|---|---:|---:|---:|
|open2.5→call|0.274488027381|BB|5|47.5|9.5|
|limp→check|0.170310830122|BB|2|49|24.5|
|limp→raise2.5→call|0.107457082024|SB|5|47.5|9.5|

History `raise_to_5` uses chips with BB=2chips, hence 2.5BB. Reach is the product
of every seat's own public-history action probabilities; class chance removes
shared cards, and full concrete-deal summation independently checks board chance.
The last preflop decision actor is labelled hero; physical BB/OOP acts first on
flop regardless of hero orientation. RootSB signs reverse BB-hero EV intervals.

Opponent range features integrate the **distribution** inferred from public
history, own cards and flop. They never input the actual opponent private card.
Own range cancels conditional on own cards. Joint type moments retain correlated
private chance and card removal. Existing exact hole/runout kernel and standalone
behavioral street CFR/BR are reused, with no old solver/policy update.

Nominal flop fractions1/3,1/2,3/4 are capped, minimum bet1BB, duplicate amounts
removed. Pot2 therefore has actual bets1 and1.5BB; pot5 has5/3,2.5,3.75BB.
One legal3x raise is allowed; turn/river check through. Fractions can be changed within the existing maximum of3distinct bets
(native child stride4). A fourth distinct bet or later streets requires further
engine changes; neither is claimed implemented.

## Cohort vs full physical chance

410previous suit-orbits excluded from new7train/7validation/7final, seven nontrip
structures, seeds23003/24001/25013. Trips remain in the eight population strata.
Each board is solved locally from uniform initialization at512 and2048 sweeps.
Both budgets always reported; no candidate choice. These are board-specific
solutions, not zero-shot generalization of a globally trained policy. Cohort
NashConv averages are equal-board diagnostics, not true-chance full-poker NC.
Final acceptance mean<=.05/worst<=.1BB and no increase vs512, without retuning.

Full22100physical-board conditional chance is computed for each prefix before
any new study EV. Its eight-stratum allocations and PRNG draws(seed26003 plus
fixed stage offset) are locked in design.json. Population uses fixed uniform512,
**not** the2048 final profile.128IID draws with replacement per prefix; repeated
boards retain multiplicity but are unique in exact probability coverage.

96additional prefix/board events maximize conservative uncomputed interval-width
reduction for a fixed event count, by sorting `P(prefix)*P(board|prefix)*100BB`.
The selection uses no EV, NC, or final outcomes. Ties use prefix/card order.
All96fall in open→call. Priority results affect deterministic bounds only;
including them in the random-stratum mean would introduce selection bias.

## What the intervals mean

Existing weighted Hoeffding/multiplicity evaluator is reused. Only profile EV is
scaled to the registered tree's terminal support B:13.75BB for pot5,5.5BB for
pot2. Its range2B is used for sampling error; local game-value bounds remain
±pot/2 from legal check/fold guarantees. New family99% uses12one-sided tails
(3prefixes×profile and game lower/upper). Local exact BR width, population
sampling error, numerical roundoff and unknown real-game error are separate.
Raw unnormalized deal-mass comparison has a pre-fit absolute1e-7 guard; its
roundoff diagnostic is not measured in BB. EV/export comparisons remain1e-12.
Numerical1e-7BB guards are not formal interval-arithmetic proofs.

For fair before/after deterministic accounting, **every unevaluated board stays
at±50BB**, even when registered restricted-tree support is narrower. Exact known
contributions use actual probabilities, never zero-imputation. Additional model-
support-only root bounds are labelled posthoc decomposition, not measured
real-poker precision or a replacement acceptance criterion.

Root keeps prior two CALL profile results and adds the three new fixed512
profiles. Fold terminal contribution is exact; other matched leaves stay±50BB.
Old family failure1% plus new1% yields joint root98% by union bound, not99%.
The new conditional profiles define the target; this is not the original complete
frozen preflop payoff, preflop best response or equilibrium. A bound on an
unevaluated branch is not a bound on approximation error in evaluated branches.

## Reproduction and restart

System Python/C++17; no new dependency/service or billing setting:

```
python -B -m unittest tests.test_call_coverage -v
python -B -m gto.abstract.call_study --phase design --build-dir /tmp/call-design --chance-output /tmp/call-chance.json --output /tmp/call-design.json
python -B -m gto.abstract.verify_export --actual /tmp/call-design.json --expected docs/qa/call-coverage-20261105/design.json
python -B -m gto.abstract.call_study --phase cohort --build-dir /tmp/call-cohort --output /tmp/call-cohort.json
python -B -m gto.abstract.call_verify --actual /tmp/call-cohort.json --expected docs/qa/call-coverage-20261105/cohort-results.json
python -B -m gto.abstract.call_study --phase population --build-dir /tmp/call-pop --cache-dir /tmp/call-cache --output /tmp/call-population.json
python -B -m gto.abstract.verify_export --actual /tmp/call-population.json --expected docs/qa/call-coverage-20261105/population-results.json
```

Fresh output paths required; committed source/protocol/chance/design hashes checked
before evaluation. Atomic complete-cache identity/checksum rejects stale rows.
Current durable cache:/workspace/gto-call-population-cache. No independent automatic
restart. Population known boards are not called unseen; next unseen study must
exclude the updated registry in population-results.json. Preserve failures and
do not select or refit on these final results.

## Observed batch results

Final21contexts(7boards×3prefixes): uniform512 mean/max NC.028708221/.067082797BB;2048 .008114711/.020393470. Both21/21below.1, all3preregistered convergence criteria PASS. No final tuning. New population+priority479unique prefix/board contexts all below.1 with512; this does not repair the prior vs3bet/vs4bet512profiles, whose saved worstNC.363559/.361102 remain unaccepted.

|New prefix|Unique evaluated boards|Actual conditional probability|512worstNC BB|Population profile99%interval BB|
|---|---:|---:|---:|---:|
|limp→check|127|0.578104%|.021378|[-2.071649,1.605540]|
|limp→raise→call|128|0.579580%|.065465|[-5.464403,3.733953]|
|open→call|224|1.056529%|.072419|[-5.166071,4.018774]|

128random draws perprefix plus96priority events; limp→check has one repeated
random draw. Exact coverage counts127,not128. Priority96are excluded from random
mean/radius and included in deterministic coverage. Chance-only priority score
predicted0.130982031BB conservative width gain for those96events.

CALL-prefix evaluator support probability2.628777%→57.854371%; actual computed
root-board event probability.015370%→.466112%,not57.85%computed. Conservative
deterministic root interval before[-29.488759480,29.377962812],after
[-29.261958064,29.154022268]BB; width decreases.450741960BB with SAME±50
unevaluated support. Remaining wholly unevaluated CALL prefixes1.027721%.

Statistical root interval prior99%[-28.687245232,28.500944718],new joint98%
[-3.038183245,3.060236342]. These confidence levels and specified continuation
sets differ; not a same-policy real-game accuracy comparison. Posthoc model-
support-only interval[-7.262903076,7.076602562]shows that part of the tightening
comes from the restricted game assumption, before population EV sampling.
All3registered root criteria PASS. Model approximation and external deviation
remain UNKNOWN; no new normal GTO range or formal acceptance.

Local new13tests PASS; previous73tests retained for new-head CI. One initial small
feature fixture violated the existing full-prior guard; fixed to use full legal
unknown-opponent support,guard preserved. EV/provenance compare1e-12; raw
unnormalized chance-mass diagnostic uses its existing1e-7native guard with a
separate verifier test, not relaxed EV tolerances.

New unseen registry674suitorbits includes all cohort/population observations.
Source,design,data and protected dependency hashes are in dependency-manifest.json.
Latest-head CI is pending at result commit; final receipt and PR record actual
conclusions. No main/production/SSO/fees changes; no independent auto restart.

# Restricted continuation quality audit

Actual frozen HU50BB flop_controller preflop policy; exact compatible-hole
posterior and all990runouts. No original policy/controller/demo changed.

## Theory
4arms are complete plans selected ONCE at the player own abstract signal.
This preserves within-hand correlations. Arm parameters are not averaged.
Original sampled learner updates both seats with correct opposite payoff signs,
but visit-weighted averages and shuffled context updates are NOT synchronous
full Bayesian type-game sweeps; do not apply a standard full-game convergence
claim to those prior descriptive experiments. Its heldout EV is not NashConv.

Public-board identity is intentionally abstracted by own key. This defines a
restricted signal/type Bayesian normal-form game. Players could use more
information/actions in actual NLHE. Not full public-board NLHE infosets.

New tensor A[i,j,a,b] already includes exact joint chance. Each sweep computes
hero U[i,a]=sum(j,b) A*q and villain V[j,b]=-sum(i,a) p*A.
Both regrets update from the SAME pre-update profile. Strategies are averaged
uniformly across sweeps for EVERY own type, not by sampled type visits.
BRhero=sum(i)max(a)sum(j,b)A*q. Max must stay OUTSIDE opponent type sum.
BRmin=sum(j)min(b)sum(i,a)p*A. NashConv=BRhero-BRmin; restricted
exploitability=NashConv/2 (two-player zero-sum convention only).
Positive cumulative external-regret sum/T is independently checked as an
upper bound. Numeric guard1e-7BB; no Monte Carlo evaluation error.

## Predeclared train/evaluation split
Train Ac7d2s,Ts9s8s, equal research weights. These are NOT real flop chance.
Heldout Kc8d2h,QcQd3s,JcTc9d,7c5c3c chosen before execution. No heldout
tuning/seed selection. Seeds17/29 control initial policies only. Exact heldout
evaluation has no seed and needs no sampling CI. Neither heldout values nor
its regrets update trained policy. Both seeds retained.

|stage|seed|NashConv at1|at1000|at100000|restricted exploitability|
|---|---:|---:|---:|---:|---:|
|vs_3bet|17|7.549171611|0.037289708|0.002681238|0.001340619|
|vs_3bet|29|7.235480413|0.036867139|0.002684108|0.001342054|
|vs_4bet|17|16.528853936|0.057270893|0.004098525|0.002049263|
|vs_4bet|29|13.726865181|0.053987842|0.004050761|0.002025381|

Target<=.01BB achieved4/4 initialization runs in2restricted training games.
This is NOT formal Poker ID acceptance. Full curves include1,10,100,1000,
10000,100000sweeps. Figure convergence.svg plots these stored data.

## Legacy model on the same joint training game
Legacy models were trained separately on one board/sampled worlds; new models
train the declared two-board mixture/full chance. The following comparison
measures final quality on a common target,not a controlled causal ablation.
vs_3bet: old frozen policies NashConv range1.309011094..2.787821901BB.
vs_4bet: old frozen policies NashConv range1.367022135..5.257459533BB.

## Heldout board results
|stage|seed|flopIDs|restricted NashConv BB|unknown own-type mass(hero/villain)|
|---|---:|---|---:|---|
|vs_3bet|17|[44, 25, 2]|3.047244262|0.0/0.0|
|vs_3bet|17|[40, 41, 7]|0.677710774|0.0/0.0|
|vs_3bet|17|[36, 32, 29]|1.278005320|0.0/0.0|
|vs_3bet|17|[20, 12, 4]|1.159523051|0.0/0.0|
|vs_3bet|29|[44, 25, 2]|3.048306347|0.0/0.0|
|vs_3bet|29|[40, 41, 7]|0.677905886|0.0/0.0|
|vs_3bet|29|[36, 32, 29]|1.278124862|0.0/0.0|
|vs_3bet|29|[20, 12, 4]|1.159475827|0.0/0.0|
|vs_4bet|17|[44, 25, 2]|0.944653594|0.0/0.0|
|vs_4bet|17|[40, 41, 7]|0.584754117|0.0/0.0|
|vs_4bet|17|[36, 32, 29]|2.024112009|0.0/0.0|
|vs_4bet|17|[20, 12, 4]|0.404478796|0.0/0.0|
|vs_4bet|29|[44, 25, 2]|0.943738835|0.0/0.0|
|vs_4bet|29|[40, 41, 7]|0.581736291|0.0/0.0|
|vs_4bet|29|[36, 32, 29]|2.028417598|0.0/0.0|
|vs_4bet|29|[20, 12, 4]|0.398483968|0.0/0.0|

Heldout NashConv remains about0.398..3.048BB despite no unknown type mass.
Generalization is NOT accepted. No re-training/tuning on these results.
The current own-feature/public-board abstraction does not establish a policy
equilibrium on changed board distributions. External GTO deviation UNKNOWN.

## Fixed opponents and research leaf
Uniform,4pure arms,and own-strength heuristic:6fixed opponents,both seats.
Report baseline profile,exact best response and unilateral gain independently.
Equilibrium policy need not be maximally exploitative against each different
fixed opponent; these gains are not its selfplay NashConv. See JSON details.

research_leaf exports actual-flop169x169 class-pair net payoff with compatible
hole counts. Cells have NO preflop range weighting. SB-chips conversion uses
2chips/BB and negates/transposes heroBB. Zero-count cells are UNREACHABLE,
their0placeholder is not an EV estimate. Weighted leaf/gamematrix reconciliation
checked for all24board-stage-seed exports. Class coverage is recorded honestly.
The hook is research ONLY. Original CFR is not updated; true public-board
chance integration and broader continuation validation are still missing.
Do not pass equal selected-board weights as real CFR chance.

## Reproduce
python -B -m unittest tests.test_continuation_game -v
python -B -m gto.abstract.continuation_quality --build-dir /tmp/quality --output /tmp/quality.json
python -B -m gto.abstract.verify_export --actual /tmp/quality.json --expected docs/qa/continuation-quality-20261031/results.json
Strict1e-12 scalar/source identity; no dependency downloads/new packages.
Formal0/12, normalGTO release0, UI added ranges0. Model approximation and
external GTO errors UNKNOWN. Existing oldQA artifacts are not rewritten.

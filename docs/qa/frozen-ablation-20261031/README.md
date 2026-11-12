# Real frozen HU50BB model measurements

Actual immutable packet/kernel data,NOT the synthetic unit fixtures.
Input: seed1701 frozen preflop policies,seed700017 heldout kernel,S256.
Card-removal mass:1624350 compatible ordered hole assignments.
Net BB before blinds; delta=new minus old. No strategy is updated or published.

The new toy protocols use public-board-unconditional all-in equity given
compatible preflop classes. They are NOT a specific-flop equity calculation.
Stored card-controller planes use card-dependent actions internally but are
also averages over public boards. The deterministic bet/call and raise/call
protocols are explicit experimental model parameters,NOT learned/played flop
strategies. Negative deltas do not establish real-game GTO quality.

Input packet canonical SHA256: a3e4cf9d4d1047e3a3a9dc9e7735c459c28916513cecfc1f1f5da1148788b00a
Used kernel means/exact-mask/sample-design SHA256: 41da543de6968fe51724114c6bcdf0008fb69a63f26e3bd2251949a85b0d4669
All72 reported intervals jointly>=99% under the fixed sampling design.
Shared unordered seat/plane worlds are grouped before bounding; exact terms
are constants. Model approximation error and external GTO deviation UNKNOWN.

## Entire facing decision node

Full frozen fold/call/raise strategy and subsequent preflop responses included.
Each row is conditional on reaching that decision,NOT winnings per dealt hand.

| Frozen preflop policy | Stage | Checkdown BB | Stored card controller BB |
|---|---|---:|---:|
| checkdown | vs_3bet | -1.306166848 | -0.776877287 |
| checkdown | vs_4bet | -5.059230600 | -9.332974517 |
| flop_controller | vs_3bet | -1.416131371 | -1.293614972 |
| flop_controller | vs_4bet | -4.124912556 | -5.042426469 |

| Frozen policy | Stage | New experimental protocol | New BB | Delta vs stored card controller BB | Sampling interval |
|---|---|---|---:|---:|---|
| checkdown | vs_3bet | bet_call | -1.437997732 | -0.661120445 | [-0.833939012572762, -0.48830187699842015] |
| checkdown | vs_3bet | raise_call | -2.659135502 | -1.882258216 | [-2.10741211150366, -1.6571043196525805] |
| checkdown | vs_4bet | bet_call | -10.563139991 | -1.230165474 | [-1.9013607921629567, -0.5589701548735371] |
| checkdown | vs_4bet | raise_call | -12.659867377 | -3.326892860 | [-4.017086623518262, -2.6366990970058803] |
| flop_controller | vs_3bet | bet_call | -1.822379438 | -0.528764466 | [-0.6371071180941855, -0.42042181409772983] |
| flop_controller | vs_3bet | raise_call | -2.798735507 | -1.505120535 | [-1.656210722709755, -1.354030347923799] |
| flop_controller | vs_4bet | bet_call | -5.080639727 | -0.038213258 | [-0.2776506314500915, 0.20122411607359927] |
| flop_controller | vs_4bet | raise_call | -5.444726268 | -0.402299799 | [-0.6562768030112643, -0.14832279531089945] |

## Direct CALL continuation only

Conditioned on full history AND hero CALL. Pot18/42BB,remaining41/29BB.
This denominator differs from the facing-node table; do not interchange them.

| Frozen policy | Stage | Checkdown BB | Stored card controller BB | Difference BB |
|---|---|---:|---:|---:|
| checkdown | vs_3bet | -1.636488602 | -1.477898407 | 0.158590195 |
| checkdown | vs_4bet | -7.118717994 | -12.646348549 | -5.527630556 |
| flop_controller | vs_3bet | -1.425800790 | -1.354559537 | 0.071241253 |
| flop_controller | vs_4bet | -3.882699356 | -7.610155045 | -3.727455689 |

Pure-protocol parameters and all72intervals are in refined-results.json.
Facing4bet raise-to29BB is a short all-in,not an impossible63BB investment.
All-in/fold payoffs are retained,preflop policy frequencies remain frozen.

Reproduce after existing precision workflow rebuild:
`python -B -m gto.abstract.frozen_ablation_study --kernel <precision-study/rb-kernel.json.gz> --output /tmp/frozen-ablation.json`
Without --kernel,the committed original packet kernel is used; that is a
different legitimate baseline dataset,not the refined-results golden file.

The native C++ evaluator independently checks complete decision-node values.
regression-replay.json is explicitly SYNTHETIC UNIT ORACLE ONLY and must never
be used as measured policy EV evidence. Formal acceptance remains0/12.

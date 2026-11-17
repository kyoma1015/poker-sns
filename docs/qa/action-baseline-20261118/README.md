# HU50 corrected-average variance-reduction gate — FAIL / STOP

Source: 78368cb44dbe2c25c83c96666b0ec33b269019bf. This is isolated HU50,
zero ante/rake research, not approved release specifications. The corrected
average checkpoint, suit canonicalization and RNG fixes are reused unchanged.
Original files, frozen CFR, HU1BB and eight BLOCKED_UNVERIFIED candidates remain
protected. Formal acceptance stays **0/12**, verified RFI **0**, verified 3bet **0**.

## Predeclared comparison and actual result

See PROTOCOL.md. Four arms warm-import identical R/S/RNG, same master seed,
2-second target / 512-pair ceiling. Atomic pairs may overrun slightly. Separate
frozen 3-seed diagnostics do not update regrets. Artifacts total under 4MiB
(20MiB storage ceiling). No expanded training: every native improvement gate failed.

| arm | pairs | seconds | positive average samples at RFI / vs3BB / vs10BB |
|---|---:|---:|---|
| zero-standard | 374 | 2.0005 | 374 / 1 / 0 |
| baseline-standard | 343 | 2.0057 | 343 / 1 / 0 |
| zero-reach | 320 | 2.0364 | 320 / 97 / 25 |
| baseline-reach | 288 | 2.0002 | 288 / 88 / 25 |

Full-support proposals retain every legal size and correct both actors' pi/q,
including zero target probabilities. Fixed action predictions use acting-seat own
cards and public history only, never future cards. Native terminal payoffs remain
the target. Independent finite CF-vector/average oracle verifies expectation.
Combined/control frozen CF-vector sample-dispersion ratios across seeds are
0.052, 0.559, 0.176. This is empirical variance evidence, not a regret bound.
Baseline alone was inconsistent. Reach sampling increases deep preflop samples
but does not yet improve policy quality. R/S update revisit rates in the four
new stages are about 14–16%; counts and definition are in comparison.json.

## Independent native policy measurement

Six profiles, same 32,768 deals/action streams each: 196,608 actual native State
paths in 51.2655 seconds. Eleven simultaneous empirical-Bernstein intervals have
family confidence 99.9%. The digest for each frozen profile is in native-paired.json
and the corresponding checkpoint. All are total legal policies via the existing
full-support policy definition; none is accuracy-qualified.

| averaged policy | SB EV BB | 99.9% family interval | immediate-fold gain lower BB |
|---|---:|---|---:|
| control | -3.506119 | [-4.496421, -2.515817] | 2.015817 |
| action baseline | -3.612793 | [-4.601847, -2.623739] | 2.123739 |
| reach sampling | -3.666031 | [-4.655224, -2.676838] | 2.176838 |
| combined | -3.528519 | [-4.518352, -2.538686] | 2.038686 |

Combined minus control: **-0.022400 BB**, interval **[-0.551464, 0.506664]**.
No statistically demonstrated improvement; immediate-fold weakness remains.
Previous lower bound 1.424181BB uses different sample allocation/confidence
family and cannot establish a before/after performance change. Current-regret
extraction was also predeclared: combined/current-control delta -0.063614BB,
[-0.821826, 0.694598]; no gate passed. Extraction is not average convergence.

Immediate-fold positive gains also bound full best-response improvement and
zero-sum NashConv from below. **Complete BR upper, NashConv point and upper remain
UNKNOWN/null.** Restricted first-decision action enumeration is included but its
upper intervals near 99BB are uninformative and are not complete BR bounds or
convergence evidence. No trivial physical cap is substituted for a measurement.

## All169/action conditional estimation

Fresh validation uses seed17118091, distinct from the old action-prediction
artifact's seed17112026. Four worlds per class; common deal/tape scheme. Conditional
reports use independent reference betting plus native terminal rank, not a full
native State rollout (the root study above does use native State throughout).
Exact card-removal integration of opponent fold/call probabilities conditions
all-in estimates on calls. Non-all-in paths integrate the last binary all-in
policy coin. Finite oracle tests check expectation and conditional variance.

For the combined policy, 338 forced-fold cells across RFI/vs3BB have exact EV
interval width **0 instead of 100BB**; 338 all-in cells have support-limited width
about **50 instead of 100BB**. Mean interval width is 98.48485BB (RFI) / 98.38710BB
(vs3BB), maximum still **100BB**. Root class-weighted interval width remains
**26.528742BB**. This limited improvement does not pass all169/action precision.
Conditional RFI EV -3.254325BB [-16.518696,10.010046]; vs3BB EV 1.452718BB
[-11.827883,14.733319]. Different estimators' n=4 point values are not evidence of
strategy improvement. There is no surrogate continuation model; a uniform
native/reference discrepancy bound and full conditional error bound are UNKNOWN.

Pilot files reuse the prediction artifact's seed and are explicitly marked
NOT_USED_FOR_CI_ADMISSION. They are not independent quality validation. Fresh
files retain the actual evaluation seed and last action-tape seed separately;
an output-field shadowing issue was corrected without changing sampled worlds.

## Tests and resumption

Local new regressions only:
`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_action_baseline gto.qualification.test_conditional_action -v`
**8 PASS** (focused-tests.txt). They cover arbitrary baselines, opponent pi/q,
zero-target average support, warm-state preservation/resume, public sizing,
card removal, conditional/native terminal expectation and restricted-BR target.
Old successful QA/CI was not manually rerun. New automatic qualification CI adds
these tests to the existing suite. No TS/UI changes; local app build/lint/browser
not repeated. CI is not a strategy-quality certificate.

Commands: `python -m gto.qualification.action_baseline_study --help`,
`python -m gto.qualification.action_native --help`,
`python -m gto.qualification.conditional_evaluate --help` show invocation arguments; compute limits are fixed in the protocol and modules.
All six checkpoints are gzip JSON snapshots with R/S/RNG and policy digest;
`action_native.load_solver(path,native)` restores one. Resume is manual, not
automatic. Next work must address the positive fold-deviation evidence and heavy
importance weights before another predeclared small gate; do not expand any
failed arm or register it. Full BR/precision/specification gates remain mandatory.

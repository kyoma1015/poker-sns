# PR120: full-history strategy GENERATION, bounded first solver gate

2026-11-17 JST. Starting `d3507b681b186d2e52e8a9217bee786bdf0a1b47`,
remote PR Open/Draft verified. Existing8CI families SUCCESS; no manual rerun.
Only qualification solver/experiment files and its test workflow changed.
No UI, formal specification, frozen policy, historical checkpoint, candidate,
HU1BB calibration or registry mutation.

## Actual solver delivered

`native_mccfr.py` implements tabular outcome-sampling MCCFR on full52-card HU50
reference betting, independently replayed against existing native State. It uses
existing matched-history regret matching and PublicResponse exact observations.
Each sampled trajectory reaches real settlement across all streets; no continuation
surrogate, turn/river truncation, sparse action set or default fold. Both players
are updated, exploration0.6 for the traverser, opponent sampled from its target.
Sampled counterfactual gradients use own-prefix and suffix importance weights;
separate average sums use own reach / sampling-prefix reach. No weight clipping.
A deterministic uniform-all-legal generative prior covers every unseen exact
information set, including arbitrary native raise-to histories. This IS a total
behavioral policy definition, NOT evidence that every row is learned or accurate.
Unseen histories are not represented as solved CFR rows.

256 paired iterations (512 sampled learning trajectories),0.777803s,
1022 visited information sets. One algorithmically complete unverified policy;
zero fully trained/qualified full-game policies. Regret/average values actually
change. All169 hand classes have sampled frequency and all-action EV records.
All legal root99actions and all BB responses/SB re-responses remain supported;
3BB open ->10BB3bet ->SB response and3BB ->45BB ->50BB short all-in replayed.

Policy digest:
`6bb5c89a082769c27f2b593b41e8c848995cb98c547476a86f5e52f1ba65dba5`
Policy identity covers game/prior/algorithm, source pins and normalized average
rows. Snapshot also preserves regret sums, average sums, iteration and RNG state.
JSON checkpoint restore reproduces uninterrupted training exactly in regression.
Digest binds a policy definition; it is not a quality certificate.

## Measurements on exactly that frozen policy

Final evaluation22.563812s;169classes x4worlds x(99+93)actions =129792
complete reference rollouts. All actions use common worlds/random tapes. Two
worlds select a class-only pure root response and two independent worlds measure
it. This is a feasible one-decision deviation, NOT complete downstream BR.
vs3BB: exact opener reach0.010070079159174442 and BB-class/card-removal posterior,
including within-class rejection sampling. Posterior weights sum1 and have an
independent direct card-removal test. Conditional gain scales by this reach for
root interpretation. It is not the uniform-range forced-open pilot.

| quantity BB | RFI / SB | vs3BB / BB conditional |
|---|---:|---:|
| profile EV mean | -4.268624471 | 1.559057188 |
| simultaneous conservative EV interval | [-17.532996,8.995747] | [-11.705309,14.823423] |
| class-only response held-out EV | -3.530165913 | 1.494212284 |
| paired held-out gain | 1.005354434 | 0.240376365 |
| gain interval | [-36.511953,38.522661] | [-37.276916,37.757669] |
| complete BR EV upper (physical range only) | 50 | 50 |
| complete BR gain upper (physical range + EV interval only) | 67.532996 | 61.705309 |

The response gain uses the held-out baseline, not the all4world baseline.
Intervals: familywise99.9% Hoeffding union budget100000; per-class/action intervals
remain extremely wide. Per-class frequencies and forced-action EV means use
separate averages; suit-specific policy covariance means multiplying their class
means is not generally the true baseline EV. They are research records, not
registry-ready frequency-weighted EV exports.

Full optimized BR and full-game NashConv point estimates: UNKNOWN, not computed.
NashConv upper100BB is the trivial zero-sum payoff ceiling, NOT measured convergence.
No claim of improvement relative to the old limited-game0.9321071527220774BB.
No surrogate continuation model is used (model substitution error0 structurally),
but uniform native/reference execution discrepancy is NOT proved, and statistical
conditional-EV error is bounded only trivially by100BB. Sampling/learning errors
are not0. This fails the numerical qualification gate. No promotion or more
population learning follows this failed small gate.

`evaluation.json.gz`: deterministic gzip JSON with all169/action values,
intervals, class frequencies, policy/checkpoint/source identity and blocked result.
`native-replay.json`:256 full-native/reference paths on that SAME policy digest;
additional16HU50 short-all-in paths passed. `training.json`, `checkpoint.json`,
`python-tests.txt` and `node-tests.txt` preserve actual outputs.

## Verification / budgets / restart

Before compute7.2GiB free; planned training<=30s, evaluation<=90s, storage<=20MiB.
Final evidence2.8MiB. Training checkpoint written every32iterations and at stop;
path length capped512 decisions. Exact-resume test, estimator expectation versus
independent matched-history CF vector, all-size re-responses, source posterior,
and native settlement tests PASS.21Python total (5new+16existing), Node8PASS;
old release evidence hashes and layout unchanged, git diff --check PASS.
No TS/UI/package changes: npm ci/build/lint and browser/mobile QA not repeated.

```
python -B -m gto.qualification.build --directory /tmp/poker-public-response-build
QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_qualification gto.qualification.test_public_response gto.qualification.test_native_mccfr -v
python -B -m gto.qualification.native_mccfr --build /tmp/poker-public-response-build --output /tmp/new-checkpoint.json --resume docs/qa/native-mccfr-20261117/checkpoint.json --iterations 288 --seconds 30
python -B -m gto.qualification.mccfr_evaluate --build /tmp/poker-public-response-build --checkpoint docs/qa/native-mccfr-20261117/checkpoint.json --output /tmp/new-evaluation.json --samples 4 --seconds 90
node --test --test-isolation=none tests/gto-release.test.mjs
```
Resume command is a manual reproducible entry point, not an autonomous scheduler.
Do not overwrite the saved checkpoint or repeat broad training without a reason.
An interrupted evaluation can be restarted within its short fixed budget; it is
not claimed to resume its RNG/partial action matrices automatically.

## Remaining release gates

Formal0/12 ->0/12, normal verified RFI0/3bet0;8legacy candidates/1352rows remain
BLOCKED_UNVERIFIED. None of1RFI,2vsopen,3vs3bet,4all169,5EV,6MTT/ring,
7players2–9,8stacks,9positions,10ante/rake,11sizes,12search is formalPASS.
A/B/C remain unapproved; no formal20stack/all-size/rake/ante numbers invented.
Old unavailable-session disk/DB/ZIP are still not recovered; accessible saved
GitHub artifacts and this new checkpoint are distinguished from missing originals.

Next engineering bottleneck is sample efficiency: exact own-card/public-history
rows are almost all unrevisited, giving high-variance importance-weighted updates
and mostly prior continuations. Improve reuse without merging distinguishable
information sets, establish a tractable independent full-response bound, and run
paired fixed-budget before/after gates. Do not label the uniform prior 'trained'.
FullBR, all169/action EV precision, uniform execution/error bounds and approved
conditions must all pass before certificate/registry/search connection.
Production/main/DB/Storage/Vercel/SSO/fees untouched; Draft maintained.

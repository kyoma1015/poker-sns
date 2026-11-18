# HU50 root-cause isolation and first-decision external gate

**Implementation tests PASS; full-native accuracy gate FAIL / STOP.**
Source c0ca9f2058f05b21c832695034efad0445e4ff25, PR120 Open/Draft. Existing
checkpoint and research evidence are unchanged. No normal registry admission,
formal acceptance remains **0/12**, verified RFI **0**, verified 3bet **0**.
Eight legacy candidates remain BLOCKED_UNVERIFIED. Formal20stack/full-size/
ante/rake proposal decisions remain PENDING; no specification was adopted.

## What was checked, and what remains a hypothesis

New six-card blind poker independently accounts for SB0.5BB/BB1BB, fold receipts,
limp/3BB open/10BB3bet, called showdowns, card removal and conditional-to-root EV.
SB fold net is -0.5BB; BB fold vs3BB gives SB+1BB; SB fold vs10BB costs3BB.
Called native HU50 shove returns net +/-50BB or0, not the gross100BB pot.
Native State and reference betting agree with independent ledger fixtures.

Both the actual production ActionBaselineSolver collector and new first-external
collector are adapted to this finite game. Exhaustive hidden-world/random-plan
integration matches independent full-tree CF-vector and realization-average sums.
The test includes arbitrary action baselines and opponent proposal != target.
Independent private-plan enumeration matches complete finite-game BR; maximization
happens AFTER integrating hidden cards, not clairvoyantly per world. Exact
checkpoint continuation is tested for OS/external/exact and native first-external.

**No payoff-sign, EV-baseline, chance-removal or update-formula defect was found
in these tests.** These finite fixtures do not prove correctness of every native
public history or rule out all sampling bias. No new defect was patched into old
frozen solvers. The strong measured issue is insufficient policy coverage and
very heavy importance weights; its complete causal share is not identified.

## Frozen full-native attribution (new diagnostic, not training)

Source policy digest:
`a4c0f1f50290d6908157a34d05fb67878c4a6d9ecd61f014ad7a0426d8b344c9`.
Four factorial profiles use the same8192deals/action tapes each (32768native paths,
10.3791sec), seed17118034, eight simultaneous intervals, family99.9%.
Learned-row ablations replace only learned rows with uniform-all-legal; unseen
prior remains unchanged. There is no fold completion or passive fallback.
Each intervention has a separate digest. None is proposed as a release strategy.

- 8121/8192 paths (**99.1333%**) visit an average-untrained row.
- Root average has145/169classes, **89.2911%** of true card-combination mass.
  Root regret has160/169classes. New-stage root update maximum is8; ancestor
  counters were reset by the previous experiment, so this is not lifetime count.
- All postflop decisions observed in this sample use untrained-average rows.
- First-untrained partitions contribute SB root EV: SB/preflop -0.218506BB,
  BB/preflop -2.471313BB, BB/flop -0.002014BB; fully positive-S paths +0.002808BB.
  Sum=-2.689026BB. This is a decomposition of observed loss, not a causal effect
  of independently changing those subsets.
- Both-uniform profile SB EV=-3.629944BB; fold-deviation gain lower1.063518BB.
  Thus the generative prior itself is exploitable before any learned updates.
- Learned-both minus uniform-both EV +0.940918BB, interval[-0.816401,2.698237].
  Learned BB's effect with learned SB: -0.005615BB [-0.643049,0.631818].
  Neither demonstrates a significant learning gain or proves absence of effect.

Frozen1024path sampling probe, no R/S/masterRNG changes (0.756sec): median /p99/max
absolute regret increment per path =490.54 /2,135,380 /45,597,322;
maximum average weight per path =41.21 /68,332 /1,861,115. These mixed-infoset
summaries are not global ESS, regret bounds, or a bias estimate.

Evidence supports **unconverged, largely prior-driven continuation with extreme
importance variance**. It does not establish an exclusive cause or universal
correctness of the existing engine. More iterations alone are not authorized by
this conclusion; any new method must pass bounded independent native comparison.

## Equal-wall-budget finite convergence comparison

One second/method/seed (complete atomic iteration), identical initial state and
chance law. Independent exact BR of average policies gives:

| seed | OS NashConv BB | external BB | exact CFR BB |
|---|---:|---:|---:|
|17118031|0.038332|0.006012|0.003921|
|17118032|0.008718|0.004078|0.003597|
|17118033|0.012136|0.005371|0.004095|

Initial uniform NashConv2.211111BB. External beats OS on all3seeds in this GAME.
These are measured complete BR/NashConv points for the six-card restricted game
ONLY; they cannot be used as HU50 quality, complete BR bounds or release evidence.
All9finite checkpoints are saved. Finite full-tree exact CFR is not silently
installed as the native continuation model.

## Bounded full-native first-external experiment

After these findings, PROTOCOL.md declares a second stage: enumerate every legal
first traverser action, then reuse existing full-support sampled continuation,
control variate and all-actor pi/q corrections. No unbounded external tree expansion.
Production changes are confined to the new FirstExternalSolver subclass; existing
OS/average/baseline sources stay immutable. Both traversals freeze R until the
complete pair; independent child RNG streams and full R/S/RNG snapshots resume.

Three matched seeds, two methods, target3sec/max1024pairs; checkpoint each complete
pair. Actual wall time3.07–3.39sec includes serialization and the last atomic pair,
so this is not a core-compute-only throughput comparison. OS completed16/17/17
pairs, first-external8/9/9. Root average coverage after training is146–147/169,
versus145/169before. Total infosets grow to7210–7573 with enumeration, but this is
not convergence. A future throughput comparison needs checkpoint-overhead timing;
no unmeasured efficiency claim is made here.

Fresh independent native holdout seed17118038: seven profiles x8192worlds =57344
paths,14.9722sec,13simultaneous intervals/family99.9%. All six stage tests fail.

| seed | external - OS EV BB | simultaneous interval BB | external - frozen EV BB |
|---|---:|---|---:|
|17118041|+0.029480|[-0.777324,0.836284]|+0.132263|
|17118042|-0.011108|[-0.784653,0.762436]|+0.045044|
|17118043|-0.004944|[-0.732432,0.722544]|-0.096863|

External-minus-frozen intervals are[-0.681585,0.946111],[-0.781469,0.871557],
[-0.866662,0.672936]. Therefore **no significant decline in fold-deviation gain**.
External fold-gain intervals are[0.738006,5.035188],[0.825808,5.121824],
[0.966057,5.265389]BB, all still refuting convergence.

The old frozen-policy lower2.038686BB and paired comparison -0.022400BB
[-0.551464,0.506664] remain preserved baseline evidence. New smaller-n bounds
must not be compared directly with that lower as improvement. The frozen policy
is unchanged: new holdout EV-3.518860BB is measurement variation, not a new strategy.

Full HU50 BR upper/NashConv point and upper remain UNKNOWN/null. Positive legal
fold-deviation gains give lower bounds only. No physical100BB cap is substituted.
All169/action root interval width **26.528742BB unchanged**, reused from old evidence;
the native gate failed, so costly all169 reevaluation/expanded training was not run.
A native profile-only interval is a different estimand/allocation, not all169 gain.
Uniform continuation execution-error bounds remain UNKNOWN. No model-error-zero
claim is made for an unproved implementation.

## Tests, artifacts, commands, resumption

`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_blind_oracle -v`
New10regressions PASS (focused-tests.txt). Automatic qualification CI adds them
(43previous+10new). Old successful QA/CI not manually rerun. No TS/UI changes;
local npm build/lint/browser not repeated. New CI results are recorded in PR120.

- `root_cause.py`: finite comparison, native factorial attribution and weight tails.
- `first_external_study.py`: native training/independent holdout with fixed gates.
- `manifest.json`: protected source checkpoint hash, new source/artifact SHA256.
- `finite-*-checkpoint.json.gz`: method/R/S/RNG for restricted diagnostics.
- `outcome-*-checkpoint.json.gz`, `first-external-*-checkpoint.json.gz`: six new
  native total-history research policies; **qualified0**, ordinary registry0.

Manual resume: `rules,native=build.load(build_dir)`;
`first_external_study.load_experiment(rules,native,checkpoint_path)` restores a
new native state. `FiniteCFR(method).restore(data)` restores a finite state.
No automatic restart service exists. Source evidence and frozen checkpoint are
unchanged. Native experiments and test artifacts occupy under3MiB (20MiB cap);
actual bounded study compute is under the predeclared240sec ceiling.

Next: do not expand the failed method. Address root/continuation coverage under a
measured compute budget, accounting separately for checkpoint serialization;
retain correct hidden-card reach law. Require significant native paired EV gain,
fold-exploit reduction, all169/action precision and complete response/error bounds
before certificate/registry/search adoption. Formal specification approvals remain
separate, and formal12conditions cannot be weakened. No production/DB/Storage/
main/deploy/SSO/billing/destructive operations were performed.

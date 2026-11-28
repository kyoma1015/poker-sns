# New-only coverage, registered minimal responses and conservative preflop BR

Research only; formal0/12, external comparison NOT PERFORMED, real-game error UNKNOWN.
No frozen CFR,8ranges/1352rows,HU1BB,2–9regression or static demo changes.

## Preservation and registration

Restored execution environment; public/local base cc905fc7633fa2da07f7fe1c1c7e88adaa4ac4fa
synchronized by exact Git object reconstruction after tree equality. Original local
fa4d156 is retained at backup/gto-call-local-20261105. Reference/diff/untracked
snapshots:/workspace/gto-preserve-call-20261105. Original object store and alternates
/workspace/poker-sns/.git/objects retained. No hard reset, clean or force-push.

Protocol/source/design committed locally before study computation. Public API
commit objects are created later; local-freeze-ledger.json is not an independent
trusted timestamp. No post-final hyperparameter selection.

## New coverage and fixed profile target

256new prefix/physical-flop events,24minimum each of three high-reach CALL branches,
remaining184globally prioritized by P(prefix)*P(flop|prefix)*100BB. This optimizes
conservative unknown-width reduction for that count under the minimum quotas.
Previously evaluated events excluded; seven fresh audit suit-orbits also excluded.
Selected stages:limpcheck24,limpraisecall24,opencall208. This is full-population
importance targeting, not an unseen generalization experiment. No EV-dependent
selection and no new Monte Carlo estimate; old stratified confidence intervals
are reused unchanged, not recomputed or tightened by mixing priority observations.

Exact existing hole/card-removal/990runout kernels and the SAME fixed uniform512
street-game algorithm are reused. Native cashflow coefficients integrate a fixed
behavioral policy over public histories for each private-type pair. Only own type
indexes that player's action probabilities; actual opponent cards never enter a
decision. Coefficients are affine in showdown equity because all model actions
occur on flop before turn/river check-through. This does not support arbitrary
future-street policies without extending the model.

## Minimal response study

Known worst3cases/stage from the previous128-board study are **diagnostics**, not
unseen tests. Restore their512state by same-input recomputation, necessary because
old records store metrics rather than cumulative regrets. Check baseline agreement,
then continue the SAME regret/average arrays through512/1024/2048/4096. Stop at the
first registered checkpoint with exact private-information NashConv<=.1, otherwise
FAIL. This is minimum among checkpoints, not a proof of the minimum integer T.
7fresh suit-orbits,seed27011,exclude all674previous orbits; two stages give14fresh
cases. No final retuning. Both known6and fresh14PASS. Known budgets2048×4,4096×2;
fresh512×4,1024×9,2048×1. These are deterministic board-specific local solves.

vs3bet worst: .363558568→.207882256(1024)→.114389442(2048,FAIL)→.060724034(4096).
vs4bet worst: .361102118→.195163(1024)→.098836666(2048). Both owners' independent BR
gains shrink. Evidence supports optimization residual at512in the same restricted
game, not correction of real-poker model error. Only these6old cases are improved;
not all old256population profiles. New responses do NOT replace the fixed512
profiles used in coverage/rootEV target. Prior results remain immutable.

## Root EV and BR: two different evidence layers

Scalar reached-profile EV cannot supply class-pair payoffs for preflop deviations.
For new256only, aggregate **unweighted** concrete legal hole pairs into all169²
starting-class cells using existing type_leaf. Compute board mass per cell as
`compatible_count_on_F / (full_compatible_class_count * C(48,3))`, not the reached
scalar board probability. Preserve all class cells, including zero-own-reach
classes (their fixed profile rows are explicitly completed by uniform regret
matching, not claimed learned or GTO). SB/BB signs and transposes map to the native
preflop evaluator. Within-class suit combinations are averaged; the root BR is
restricted to169-class actions, not suit-conditional or fullNLHE BR.

Each unknown matched cell is [-50,+50]BB; fold payoffs exact. No zero placeholders.
Native evaluation at lower and upper payoff arrays gives monotone intervals for
profileEV,SBpreflopBR,BBpreflopBR(SB-value),NashConv and gain. Opponent private classes
are summed before own-class maximizing; exhaustive small-game policy enumeration
checks this, including a fixture where clairvoyant maximization would differ.
Original policy digest before/after agrees. No training of original frozen CFR.

Previous479scalar rows cannot justify off-reach class cells and are NOT rerun.
Therefore rootBRclass-kernel coverage uses ONLYnew256events(0.316974%root mass).
Fixed-profile scalarEV combines previous evidence with new data,735events across
three CALL prefixes,0.783087%root-board probability. Distinguish these coverages.

## Observed bounds and limitations

New256restricted512contexts all below.1. Root scalarboardmass.466112%→.783087%.
Same±50missing convention deterministic rootEV:
[-29.261958064,29.154022268]→[-29.102312731,28.996693152]BB;
width58.415980332→58.099005884, decrease.316974448BB.
Old98%statistical interval[-3.038183245,3.060236342]UNCHANGED; no new random sample.
Model-support assumptions and real-game error not reduced by these figures.

New-only169-class preflopBR:
- SB BR EV[-.5,49.940859969]BB;
- BB BR,expressed asSB EV[-39.646911948,11.371217703]BB;
- restricted preflop NashConv[0,89.587771917]BB.
This wide uncertainty does NOT certify convergence or prove a positive deviation.
Class/scalar EV maxdifference1.776e-15BB; new-only native/manual root endpoint
difference3.657e-9BB(guard1e-8). Numericalguards are not formal rounding proofs.
Exact calculated worlds have no MonteCarlo noise, but missing board coverage,
private/action/continuation approximation and external GTO deviation remain separate.

## Reproduction

```
python -B -m unittest tests.test_root_interval -v
python -B -m gto.abstract.root_br_study --phase design --output /tmp/root-br-design.json
python -B -m gto.abstract.verify_export --actual /tmp/root-br-design.json --expected docs/qa/root-br-20261105/design.json
python -B -m gto.abstract.root_br_study --phase responses --build-dir /tmp/root-response --output /tmp/root-response.json
python -B -m gto.abstract.root_br_study --phase expand --build-dir /tmp/root-expand --cache-dir /tmp/root-cache --output /tmp/root-expand.json
python -B -m gto.abstract.verify_export --actual /tmp/root-expand.json --expected docs/qa/root-br-20261105/expansion-results.json
```

Cache identity includes committed source/design; complete rows atomically stored
with checksums. Resume:/workspace/gto-root-br-cache. Local new8testsPASS; prior86
retained for new-head CI. Old successful CI/final evaluations not manually rerun.
Latest-headCI pending at result commit; PR/external receipt record final conclusion.
Next unseen study excludes694orbits, not674. See MVP_ACCEPTANCE.md for the12-item
source reconciliation and preflopRFI/3bet critical path, separate from postflop
research. No new normalGTO/169range UI admission. No autonomous restart.

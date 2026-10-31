# Public-history reached-range conditional feature study

Preregistered BEFORE implementation/evaluation. Protocol->implementation->
uniform/range selection lock->final report in distinct local commits,published
ordered with one ref update. No final-based model changes/reselection.

## Exact public conditional range
Read actual frozen flop_controller preflop policy and frozen_reach(after_call=True).
At each own seat,opponent class weights are the OTHER seat public action-prefix
likelihood,including the public hero CALL where appropriate. Given own concrete
holes,own prefix factor cancels. Remove flop and own cards before normalizing
each opponent concrete combo; do NOT assign uniform weight to169classes.
E= sum_legal_j reach[class(j)]*(win_ij+tie_ij/2)/(990*Z_i).
Z_i=sum_legal_j reach[class(j)]. All990turn/river boards are enumerated.
Win,tie,ahead-probability and opponent-pair equity std are audited. The std
is variation across hypothetical opponents,NOT sampling error/confidence.
ZeroZ is explicitly unreachable/None,not estimated0equity. Actual opponent
hole cards are NEVER an input to signal(own Observation,public posterior).
Each seat has a distinct posterior; role/SPR/history are preserved.

Common evaluation information is old20features +16bin reached equity +4bin
probability(pair equity>.5) +valid flag. Every comparator gets the same4arm
own-signal BR/action game. Uniform ablation ignores EVERY range-only query
field. Geometric neighbors may be cached across seeds,but probabilities never
are shared. Old frozen model is additionally re-evaluated on this new common
game; previous0.847891BB final score used OTHER boards/information and cannot
be directly compared as an identical-condition result.

## Fixed splits and candidates
Train24/validation6/final6, six public board structures. Splitseeds5519/6521/7537,
initialization17/29,teachers10000fullsweeps. All36past board suit-orbits excluded.
Equal structure weights are research,NOT actual deal flop chance. Candidate
KNN/Gaussian/hard-range-bin transfers were declared before execution.
Control=min validation mean among3uniform candidates. Range=min validation
mean among candidates whose validation worst<=control worst (predeclared
fallback if none). No final access during this choice.
Selected uniform: uniform_knn9. Range: range_knn15_r32.
|candidate|validation mean NC BB|validation worst BB|
|---|---:|---:|
|uniform_knn3|2.195898404|6.935077995|
|uniform_knn9|1.972510290|5.826363076|
|uniform_knn15|2.085062617|5.861309989|
|range_knn3_r8|1.422925173|5.066193690|
|range_knn3_r32|1.482473326|4.839880983|
|range_knn9_r8|1.378021939|4.606825513|
|range_knn9_r32|1.317871065|4.736062009|
|range_knn15_r8|1.380391161|4.223515474|
|range_knn15_r32|1.217292641|4.346028896|
|range_kernel_0.1|1.348671723|4.809078925|
|range_kernel_0.5|1.390297542|4.665734149|
|range_hardbin_knn9|1.364232193|4.062150580|

## Same locked policies on train/validation/final
Macro NC means per-board conditional NashConv averaged equally across boards,
stages,seeds. NOT full-NLHE exploitability or a population-flop estimate.
|split|evaluations/method|range mean|uniform mean|range worst|uniform worst|
|---|---:|---:|---:|---:|---:|
|train|96|0.004374620|0.828227173|0.017223406|2.737340218|
|validation|24|1.217292641|1.972510290|4.346028896|5.826363076|
|final_test|24|0.964332765|1.906589429|2.198556284|4.947173301|

|final method|mean NC BB|worst NC BB|mean restricted exploitability NC/2|
|---|---:|---:|---:|
|previous_frozen_uniform_feature|1.112047496|3.389319044|0.556023748|
|range|0.964332765|2.198556284|0.482166383|
|uniform|1.906589429|4.947173301|0.953294714|
Range mean reduction vs newly selected uniform 49.421058%; vs previous frozen model on SAME newfinal 13.283131%.
New uniform control is WORSE than the previous frozen feature policy. Do not
hide this or present the49%as improvement over the old0.847891score. Shared
teacher labels use the richer signal; capacity/transfer/target changes mean
this is a preregistered MODEL comparison,not isolated causal feature effect.

## Final acceptance and residual failure
>=20%mean reduction vs declared uniform control: PASS. Worst not increased:
PASS. Absolute worst<=0.1BB: FAIL. Overall research acceptance NOT achieved;
formal PokerID acceptance0/12. No reselection after final.
Exact specified-board evaluation sampling error0,numerical guard1e-7BB.
External GTO comparison NOT PERFORMED; real-game approximation UNKNOWN.
Teacher maxtrainingNC 0.017216801122738268BB.
Range student train mean.004375BB vs unseen~.964333BB shows residual transfer
error beyond teacher convergence. Conditional equity is not a sufficient
statistic for equilibrium responses; discretization,KNN transfer,teacher-target
aliasing are hypotheses,not confirmed causes. Current final must not be reused
as untouched test for further feature/selection changes. New uniform-control
regression needs a preregistered uniform-teacher control in a NEW study.

Fixed6opponents and both-seat BR values/gains are saved for final3comparators.
These gains are distinct from selfplayNC. All3methods use same chance/arms.
Raw representative own-card uniform/reached equities and normalizers are in
feature_audits with actual public history and opponent-reach SHA per seat.

## Reproduce
python -B -m unittest tests.test_reached_range -v
python -B -m gto.abstract.range_study --phase select --build-dir /tmp/select --output /tmp/select.json
python -B -m gto.abstract.range_study --phase final --selection docs/qa/range-generalization-20261101/selection.json --build-dir /tmp/final --output /tmp/final.json
python -B -m gto.abstract.range_study --phase audit --selection docs/qa/range-generalization-20261101/selection.json --build-dir /tmp/audit --output /tmp/audit.json
Compare each output with verify_export at1e-12+source/selection identity.
Dependency manifest pins unchanged old engine/frozen data. Final/audit cannot
fit/choose; CI reproduces original locked choice,not selection on final.
Existing CFR/8research ranges/static demo and production remain unchanged.

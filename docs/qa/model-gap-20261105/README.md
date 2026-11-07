# Independent reference, model sensitivity and actual board chance

Research-only HU50BB no-rake/no-ante, frozen preflop public prefix+CALL. **Formal0/12. External GTO comparison NOT PERFORMED; real-game approximation UNKNOWN.** Original frozen CFR,8research ranges/1352rows,HU1BB,2..9andstaticdemo unchanged. No main/prod/Storage/Vercel/otherPR/SSO/fees changes.

## Preregistration and phase isolation

142historical board suit-orbits excluded. Fresh21train/7validation/7final across7strata, seeds14843/15859/16871. Frozen predictor initializations31/43, independent rank matchup seed17881. All sets/methods/criteria committed before computation. One pre-fit clarification specifies the same probability prior for all variants; all4096sweeps, extra arm prior0. Calibration raw/bias/affine trained on train only, selected by validation MAE subject to max/stagewise MAE/one-sided regret nonincrease, then hash-locked before final. Final sensitivity7variants were fixed before all data; no final-based variant/candidate selection. Old successfulCI not manually rerun; new code requires new-headCI.

## What the reference independently checks

New C++ cash ledger traces actual investments, folds and pot settlement instead of calling the old payoff formula. It walks every concrete compatible hole assignment, integrates opponent policy BEFORE choosing own-type BR, and normalizes by OWN marginal chance. It independently aggregates conditional arm EV and class-pair leaf EV. All legal1176own holes,1271256ordered compatible pairs and990runouts/pair are used by the shared exact equity matrix.

A SECOND rank7 implementation enumerates21five-card subsets using independent count/suit/straight logic. For2preregistered physical matchups per new board it independently enumerates all990runouts.70matchups across35boards match exactly,0mismatches. This is NOT exhaustive secondary-evaluator coverage of the entire matrix; payoff/aggregation references share the existing matrix after these subset checks. Do not claim every cell has two independent equity evaluations or external GTO validation.

Max implementation discrepancies across train/validation/final:

- conditional_arm_max_implementation_error_bb: 1.31450406116e-13
- own_marginal_max_error: 1.66533453694e-16
- reference_profile_and_br_max_error_bb: 5.3290705182e-15
- base_tensor_max_error_bb: 0
- chance_direct_raw_mass_error: 1.70985003933e-10
- class_leaf_error_bb: 2.13162820728e-14
- root_attribution_error_bb: 6.43745039913e-20

These are measured floating-point implementation differences, not statistical GTO confidence intervals. Conservative numeric guard1e-7BB. Fixed-condition full integration has sampling error0; the independent rank checker covers a declared subset only.

## Conditional model prediction error and strategy effect

Four arms are complete plans:check-call,bet-call,bet-raise-call,bet-fold. They are NOT all actions/strategies in real poker. Labels are conditional on own23abstract type, fixed public board/history, against the frozen probability-control opponent. Old predictor is reused unchanged. New independent reference confirms the prediction error is not a ledger rounding bug.

Validation:

|candidate|mean arm MAE BB|max arm error|vs3 one-sided greedy loss|vs4 one-sided greedy loss|mean simultaneous greedy NC|
|---|---:|---:|---:|---:|---:|
|raw|1.519147436|21.464427822|0.816424395|0.632411508|1.226691855|
|bias|1.445658664|21.830095419|0.555336176|0.746813984|1.915370997|
|affine|1.425283349|23.848490515|0.600970761|0.881753125|2.335224583|

Bias/affine slightly reduced average MAE but worsened maximum error and vs4bet strategy loss. Both rejected by the predeclared constraints. Frozen choice=raw, not an improved predictor. The final20%MAE-improvement criterion FAILS; nonincrease flags are trivial equalities for unchanged raw and must not be presented as a correction success. No post-final tuning.

Final28contexts, raw meanMAE1.505415106BB,max19.744115711BB. vs3 MAE0.871114522,vs4 MAE2.139715691. Mean one-sided loss0.686114162BB; simultaneous greedy-profile NC1.353221314BB. One-sided loss integrates chance before max against the SAME fixed opposing controller; simultaneously switching both players is a distinct metric and not guaranteed to improve equilibrium.

|arm|final MAE BB|max error BB|
|---|---:|---:|
|check-call|1.177631244|8.634333266|
|bet-call|1.192316615|10.521465208|
|bet-raise-call|1.579487094|19.744115711|
|bet-fold|2.072225471|18.381301317|

This error includes feature/board transfer and opponent-policy mismatch. It is NOT runout sampling error, the exact-equity arithmetic error, or external GTO deviation. Prior1.547539BB used different boards; do not call the new1.505415an improvement of unchanged weights.

## Small model extensions expose large gaps

Every variant uses the same baseline23own/private partition; stack/SPR public coordinates are renamed on context changes. Range features stay at actual-reach definition to isolate chance-assumption changes. Each variant is solved at4096steps from the SAME transferred prior. Baseline4arm policy is also evaluated FROZEN under each changed model. Extra check-fold prior0. Capped all-in bets disable raising and follow the plan's call/fold bit; no illegal raise is generated. New bet fractions/stacks are explicit research counterfactuals, not changes to formal20stack/size specifications.

|variant|reoptimized mean / max NC|frozen baseline mean / max NC|max absolute model value shift BB|
|---|---|---|---:|
|base|0.007572115 / 0.042737437|0.007572115 / 0.042737437|0.000000000|
|add_check_fold|0.006630426 / 0.034152075|1.808416958 / 6.803468143|2.686031531|
|bet_one_third|0.005735067 / 0.029248587|0.437866901 / 1.150334292|2.264333364|
|bet_three_quarters|0.009390648 / 0.040666216|0.830514149 / 1.713937951|1.606334375|
|spr_half|0.002888859 / 0.023321773|0.634426959 / 1.426519887|3.141669841|
|spr_double|0.010603000 / 0.042737437|0.907411859 / 3.467372541|0.831658902|
|uniform_range|0.007363660 / 0.014503755|4.173741694 / 9.131526864|12.284855563|

All7×28=196model-specific solves below0.1BB; these are NOT196formal conditions. New-base4arm mean0.007572115/max0.042737437,28/28. Prior0.005779/max0.032241used other boards, not a direct before/after comparison.

Most material result:the base4arm strategy, despite its small own-game NC, has mean1.808416958/max6.803468143BB NC when check-fold is added in the SAME physical5plan game. Reoptimizing5plans reduces own-game NC to mean0.006630426/max0.034152075. This directly demonstrates omitted-plan sensitivity. Even the5plan game omits other plans, sizes and later-street betting, so this is NOT a bound against full NLHE.

Uniform-range strategy converges within its assumed model(mean0.007363660/max0.014503755), but evaluated with ACTUAL reach in the common5plan reference has mean2.842025284/max5.748268174BB NC. A small convergence residual does not validate a range assumption. Changed-size/SPR models have different physical actions/resources; their values are sensitivity measurements, NOT reference errors. We intentionally do not compare them as same-physics exploitability. Model value sensitivity can be12.284856BB under uniform reach, not a known real-game error bound.

## Actual physical board chance, independent of outcome sampling

For public frozen history H, compatible ordered private assignments have weight r_h(class(i))*r_v(class(j)). With Z=sum weights:
P(F|H)=Z_F/[Z*C(48,3)].
Z_F is computed by inclusion/exclusion of weighted card-occupancy moments up to3cards, not equal169class weights. All22100flops normalized. Independent direct legal-deal sums on studied boards match. Uniform-range unit oracle gives exactly1/22100; actual global class reach agrees with concrete-deal reach.

Enumerating historical boards for CHANCE normalization is not reusing them as unseen policy tests. Strategy/EV evaluation uses only the new declared splits. Full category-balanced comparator Q assigns1/(7*Ncategory) to every physical board in each non-trips category and0to trips. This is a defined all-board research comparator, distinct from the sparse selected7board distribution.

|history|sum P|TV vs category-balanced Q|TV vs physical uniform|
|---|---:|---:|---:|
|vs_3bet|0.9999999999999989|0.396539093|0.038453812|
|vs_4bet|1.0000000000000018|0.394919238|0.048827693|

Full structural probabilities and per-flop physical chances are saved in board-chance.json; all-board normalization does not imply full-board EV coverage.

## Sparse EV coverage and readonly preflop adapter

For selected boards S, raw contribution=sum_FinS P(F|H)EV(F,H), coverage=sum_FinS P(F|H). Renormalized weighted mean is conditional on F in S, NOT E[EV|H] over all boards. We save both and a conservative missing-contribution bound50BB*(1-coverage) for this actual HU50BB base model (not the SPR counterfactuals).

|stage / seed|coverage probability|equal selected EV BB|true chance conditional-selected EV BB|missing contribution bound BB|readonly root error BB|
|---|---:|---:|---:|---:|---:|
|vs_3bet / 31|0.000298187507|-1.507035598|-1.629413195|49.985090625|3.39e-20|
|vs_3bet / 43|0.000298187507|-1.507037629|-1.629415554|49.985090625|3.73e-20|
|vs_4bet / 31|0.000308406637|-7.413907856|-7.200565389|49.984579668|6.44e-20|
|vs_4bet / 43|0.000308406637|-7.413968399|-7.200617796|49.984579668|1.61e-20|

Physical board cardinality7/22100; actual probability coverage only0.029819%(vs3)/0.030841%(vs4). Missing mass~99.97%; fullEV gate FAILS. Actual selected-set TV vs equal7weights is0.051424/0.061420. Seed31 weighting shifts selected conditional EV by−0.122378BB(vs3)/+0.213342BB(vs4). These are reweighting effects on the same subset, NOT full-game EV corrections. Conservative full continuation intervals remain roughly±49.98BB, so precise full preflop EV is NOT established.

The readonly adapter independently computes class-pair conditional leaves, weights by legal class-combo counts/C(48,3), and converts heroBB to SBchips with actor-dependent sign/transpose. It verifies the preserved class-leaf kernel and a fresh contribution-only payoff array at one matchedCALLleaf. Original frozen policy is evaluated, never trained or changed. Zero other terminal leaves are linear-attribution placeholders, NOT a poker game or a fullEV estimate. Native root selected-contribution matches manual P(H)*selected conditional contribution; frozen policy digests before/after match. Do not use BR metrics from this attribution-only graph as GTO evidence.

## Tests and restart

Local `python -B -m unittest tests.test_gap_decomposition -v`:18PASS. Initial failure was a small synthetic fixture passed to a full1081-opponent helper; fixed fixture, kept production guard. Includes independent exact rank, cash/sign/all-in legality, chance card removal, generic solver parity, synthetic omitted-action counterexample and actual readonly root attribution. Synthetic test values are not measured strategy results above.

Active GTO workflow preserves39prior research unit tests and adds18newtests. It reproduces train/validation selection, ALL physical board chances, locked final sensitivity and readonly attribution at1e-12 numeric/identity checks. New-head final CI result is recorded in PR/receipt after this result commit. Full aggregate test count remains UNKNOWN if logs unavailable; no guessed sum.

```sh
python -B -m unittest tests.test_gap_decomposition -v
python -B -m gto.abstract.gap_study --phase select --build-dir /tmp/gap-select --chance-output /tmp/gap-chance.json --output /tmp/gap-selection.json
python -B -m gto.abstract.verify_export --actual /tmp/gap-chance.json --expected docs/qa/model-gap-20261105/board-chance.json
python -B -m gto.abstract.verify_export --actual /tmp/gap-selection.json --expected docs/qa/model-gap-20261105/selection.json
python -B -m gto.abstract.gap_study --phase final --build-dir /tmp/gap-final --output /tmp/gap-final.json
python -B -m gto.abstract.verify_export --actual /tmp/gap-final.json --expected docs/qa/model-gap-20261105/final-results.json
```
Use fresh output paths. Source/selection/chance hash locks prevent post-final modifications or candidate reselection. Next unseen study must exclude177used suit-orbits. Priority:complete the deterministic-plan set before trusting4/5planNE, and integrate true board chance with explicit EV coverage/checkpoints in a separate research adapter. Preserve originalCFR/8ranges/demo. External GTO reference and formal20stack/size source remain missing; fullNLHE error UNKNOWN, formal0/12. AUTO-RESUME/independent restart absent. Keep /workspace/poker-sns object source for shared local clone.

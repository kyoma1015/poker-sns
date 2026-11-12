# Matched-factorial HU50BB transfer study — 2026-11-04

Research-only, frozen HU50BB no-rake/no-ante preflop reach, vs3bet pot18/remaining41 BB and vs4bet pot42/remaining29 BB. Four complete continuation plans, exact legal hole combinations and990turn/river runouts per pair. **NOT full NLHE GTO. External GTO comparison NOT PERFORMED; real-game approximation UNKNOWN; formal0/12.** Frozen CFR,8research ranges and static demo unchanged.

## Preregistration / isolation

`protocol.json` was committed before fitting. Initially intended trips strata were found to have only2unused rank-orbits after historical exclusion; corrected BEFORE any fit to7strata,21train/7validation/7final. All72historic suit-orbits excluded, no new split overlaps. Seeds8663/9677/10687, initialization17/29,10000full sweeps per teacher. Same boards/budget/seeds/transfer for uniform20 and range23; information spaces differ intentionally. Training budgets match iterations, not CPU cost. Category experts jointly learn3training boards with absolute public-rank coordinates suppressed; interpolation mixes whole-plan probability vectors, not action parameters. Projection integrates by own marginal chance, not counts of latent types.

Nine validation cells =3methods ×(matched uniform,matched range,projected uniform diagnostic). ONE shared method minimizes pooled validation mean subject to range-worst constraint if feasible. Projection diagnostic excluded from selection. `selection-lock.json` commits raw selection SHA before final. Final uses only global_knn9, its matched controls and previous frozen range model. Final was not used for candidate selection; later oracle/error attribution never update candidate policies. KnownKcKd8s is explicitly diagnostic, not new unseen data.

## Validation and matched controls

|method|uniform mean / max NC BB|range mean / max|projected uniform mean / max|
|---|---|---|---|
|global_knn9|1.081286275 / 2.289508987|0.573371399 / 1.100191078|1.008311928 / 2.140457542|
|structure_expert_knn9|1.082585971 / 2.733362858|0.622965450 / 1.603725277|0.946243469 / 1.962789641|
|board_interpolation3x5|1.258282279 / 2.556325415|0.671256463 / 1.384265350|1.194649866 / 1.934698615|

Matched per-board teachers have uniform meanNC0.007238/max0.021531 and range0.005463/max0.018355. Chance-projected range teachers evaluated in the uniform game still have mean0.142727/max0.737458 BEFORE transfer. This demonstrates projection/target aliasing can lose equilibrium quality; it does not prove that this alone caused the previous uniform-control regression. Projected uniform happens to transfer better than matched uniform on this final set; in-sample and transferred errors are distinct.

## Locked final (28evaluations/model)

|model|mean NC BB|max NC BB|
|---|---:|---:|
|previous_frozen_range|0.732254276|3.575955718|
|projected_uniform20|0.940412319|1.890365600|
|range23|0.643153941|1.716478753|
|uniform20|1.037349595|2.529952401|

{"previous_frozen_range": {"range_mean_reduction_percent": 12.16795003347092, "range_worst_reduction_percent": 51.99944046312752}, "projected_uniform20": {"range_mean_reduction_percent": 31.609366623711477, "range_worst_reduction_percent": 9.198582878097639}, "uniform20": {"range_mean_reduction_percent": 38.00027061955692, "range_worst_reduction_percent": 32.153713542823105}}

Prior reported0.964333BB used different boards. It must NOT be compared directly as a before/after improvement. Current matched same-new-final old-policy value is0.732254BB. Final criteria: ≥20%mean reduction vs matched uniform PASS; worst not increased PASS; max≤0.1BB FAIL.2/3research criteria, overall NOT PASS. Formal acceptance0/12 unchanged.

|stage|range mean / max|matched uniform mean / max|previous frozen range mean / max|
|---|---|---|---|
|vs_3bet|0.699115032 / 1.716478753|0.970337705 / 2.529952401|0.529915888 / 0.892060144|
|vs_4bet|0.587192851 / 0.896653523|1.104361484 / 2.406621678|0.934592664 / 3.575955718|

vs3bet regresses vs previous frozen range, while vs4bet improves. Structural averages below include both stages and both initial seeds. No tuning after observing them.

|structure|range mean / max|uniform mean / max|previous range mean / max|
|---|---|---|---|
|monotone|0.594062982 / 0.778295181|0.900540122 / 0.929982256|0.570661967 / 0.595138378|
|paired_rainbow_high|0.671398538 / 0.763307421|1.767425136 / 2.406621678|2.224833671 / 3.575955718|
|paired_rainbow_low|0.422380226 / 0.626844093|0.843484501 / 0.964655262|0.580773851 / 0.645329984|
|paired_twotone|1.305746938 / 1.716478753|1.844275867 / 2.529952401|0.439877192 / 0.619556125|
|rainbow|0.625453189 / 0.700897012|0.552866486 / 0.630852129|0.441925667 / 0.628373970|
|twotone_connected|0.444946708 / 0.714860758|0.615991977 / 1.039221416|0.461279130 / 0.514759542|
|twotone_disconnected|0.438089008 / 0.487179766|0.736863074 / 0.783085364|0.406428452 / 0.430962472|

Paired-rainbow-high improves sharply, but paired-twotone and rainbow regress vs previous model. Monotone and disconnected-twotone also regress slightly. Worst new board7d7sAs ([21,23,51]),vs3bet:1.716479BB; previous0.619556BB max on that same board/stage. KnownKcKd8s audit: range vs3bet mean0.520604BB vs previous2.051703; vs4bet mean1.937457 vs2.196880. Known anchor remains poor and is NOT unseen evidence.

`error-attribution.json` decomposes exact NashConv into own-type chance-weighted deviations. KnownKcKd8s/vs4bet/seed17 largest type has mass0.080889, learned plan probabilities[0.404655,0.061578,0.022544,0.511223] but BR arm2; conditional utility[-4.545455,-3.612052,2.356411,-6.878038]BB. This type contributes0.637509BB to totalNC; it is a transferred-plan mismatch, not runout sampling noise. On7d7sAs/vs3bet largest type mass0.232882 assigns0.420555 to arm2 though arm3 is BR; contributes0.397412BB. These deviations are against the learned opposing policy, not unilateral proof of full-game GTO or a universal best plan. Exact per-type gain sum conserves totalNC (1e-12).

## Information loss vs convergence vs transfer

For coarse own information C and richer own information R, restricted-profile minimum NC measured in richer reference equals V(R,C)-V(C,R). Full-sweep asymmetric saddle bounds give certified lower/constructive upper intervals. Bounds use own holes only, NEVER actual opponent holes as policy input. Opponent cards enter only chance integration. These are reference4-plan games, not full NLHE; a finite coarse game's own NashConv can approach zero independently of this information gap.

|case|stage|uniform20→range23 minimum NC interval|range23→exact-own minimum NC interval|same range23 diagnostic oracle NC|
|---|---|---|---|---|
|validation|vs_3bet|[0.021299309,0.042246126]|[0.019336233,0.034793112]|0.009929043|
|validation|vs_4bet|[0.091582176,0.102213251]|[0.014179578,0.023369444]|0.005183161|
|final_test|vs_3bet|[0.021893792,0.031798377]|[0.008721923,0.016429214]|0.004271262|
|final_test|vs_4bet|[0.017770569,0.028991473]|[0.013723339,0.023522455]|0.005115304|
|known_anchor|vs_3bet|[0.010443306,0.041836789]|[0.018710713,0.043924103]|0.016669639|
|known_anchor|vs_4bet|[0.057644600,0.067655080]|[0.035830528,0.043458057]|0.004808523|

All6 range23→exact-own reference constructive upper bounds <0.044BB. Thus these cases show current own-information partition can support <0.1BB IN THAT richer4-plan reference; transfer still fails. Uniform→range on validation/vs4bet straddles0.1BB, so that narrower feasibility is unresolved at fixed budget. Diagnostic same-board solving yields0.004271..0.016670BB; this demonstrates restricted-game attainability on6contexts, NOT unseen transfer convergence. No positive information floor proves0.1BB impossible in those6cases; no claim for all boards, other contexts or NLHE.

## Error definitions / reproducibility

Full conditional hole/runout enumeration means sampling error0 for fixed boards/policies; numerical guard1e-7BB (floor uses2guards). Initialization variation is not a confidence interval. Equal board-stratum weights are a RESEARCH distribution, not actual board chance. There is no statistical guarantee over real-deal boards. Model approximation and external GTO deviation remain UNKNOWN/NOT PERFORMED respectively. No normalGTO UI publication; no new ranges;169coverage and8research ranges unchanged.

`analysis.json` aggregates raw scores; selection/final/diagnostic/audit JSON preserve results. `dependency-manifest.json` binds current and preserved source/data hashes. CI reproduces numeric exports at1e-12 and identity hashes. Local14meaningful tests passed including native equality, chance projection, suit isolation, information floor and gain conservation. UI build/lint and HU1BB/2..9 regressions are delegated to NEW-head existing CI; no old successful run is manually rerun.

Commands:
```sh
python -B -m unittest tests.test_factorial_generalization -v
python -B -m gto.abstract.factorial_study --phase select --build-dir /tmp/factor-select --output /tmp/factor-selection.json
python -B -m gto.abstract.verify_export --actual /tmp/factor-selection.json --expected docs/qa/factorial-generalization-20261104/selection.json
python -B -m gto.abstract.factorial_study --phase final --build-dir /tmp/factor-final --output /tmp/factor-final.json
python -B -m gto.abstract.factorial_study --phase diagnose --build-dir /tmp/factor-diag --output /tmp/factor-diag.json
python -B -m gto.abstract.factorial_audit --build-dir /tmp/factor-audit --output /tmp/factor-audit.json
```
Do not use final/known-anchor posthoc errors to choose a new model and call it unseen. Next study must preregister fresh suit-orbits after excluding107used board-orbits, or label repeated boards as development. Next implementation: learning on actual conditional expected plan utilities / value transfer rather than averaging equilibrium strategy labels; evaluate with independent fixed splits. Preserve original CFR and UI data. Formal requirements remain blocked by full-game/approximation evidence, same-condition external solution and unresolved20stack/size source; do not invent specifications. AUTO-RESUME/independent restart absent.

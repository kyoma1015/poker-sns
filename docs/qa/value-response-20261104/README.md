# Conditional-value transfer and bounded continuation response

Research-only HU50BB, no ante/rake, actual frozen public preflop reach. Same own/public23signal4complete-plan game as prior study. **Not full preflop/postflop NLHE GTO. No original frozen CFR/8research-range/static-demo edits or connection. Formal0/12. External GTO NOT PERFORMED; real-game approximation UNKNOWN.**

## Safe public baseline and isolation

Public e50a570dcb78e102b179052755f327ecdc2fc23e is the actual parent of new work. Original shadow7d3b374 at /workspace/poker-sns retained. Exact GitHub public commit object reconstructed from authenticated metadata and validated by matching its Git SHA, then checked out in separate /workspace/poker-gto-value with a shallow boundary at publicHEAD and source-object alternates to the preserved checkout. No force-push/reset/source loss. Prior6SUCCESS recognized, no manual rerun. New changes require new-headCI.

Protocol committed before learning:107historical board suit-orbits excluded, train21/validation7/final7 across7structures. Split seeds11801/12809/13829, teacher initializations31/43,10000full sweeps. Trips exhaustion documented previously; formal game scope unchanged. Equities enumerate every compatible concrete hole pair and990turn/river runouts per pair. Equal research-stratum weights are NOT real board chance.

Seven predefined candidates. Probability control and value/regret methods share the same positive-own-chance teacher support and geometry(private8/public0.5/range32,KNN9). Zero-mass targets are None, never fabricated; this actual training set excluded0zero-mass types. Values integrate opponent types/actions BEFORE max/action choice and normalize by OWN marginal chance. Villain utility sign is reversed. Regret labels are conditional instantaneous advantages EV−dot(policy,EV), not cumulative solver regret. They are targets against teacher opponents, not GTO-valued labels.

Responses use a separate native full-sweep regret-matching kernel. First iteration uses the transferred probability prior, regrets start zero, and ALL fixed64/512/4096iterations enter the average. No early stopping by testNC. This plans jointly across the restricted information game using the current public-board utility tensor; it never sees the realized opponent cards. Final decisions are functions of OWN23signal only. This is explicitly board-specific inference computation, NOT improved zero-shot generalization and NOT original CFR learning.

## Validation-only selection

|candidate|mean NC BB|worst NC BB|vs3bet mean|vs4bet mean|
|---|---:|---:|---:|---:|
|probability_knn9|0.807072278|3.097882218|0.637239336|0.976905219|
|ev_softmax_0_1|0.916950211|3.757670191|0.686454938|1.147445483|
|ev_greedy|1.184873648|6.444517481|1.221224863|1.148522433|
|positive_regret|0.977617160|3.018967154|0.749164741|1.206069579|
|response_64|0.221299321|0.574126072|0.240987429|0.201611212|
|response_512|0.040811554|0.124103370|0.047441013|0.034182094|
|response_4096|0.007884312|0.023900503|0.008822600|0.006946024|

Utility softmax, utility greedy and positive-regret transfer all worsened validation mean vs probability control. Greedy worst6.444517BB. Do not hide failures or claim a better learned EV model. Response512still failed absolute0.1BB validation worst(0.124103); response4096was selected by the preregistered stage-wise noninferiority constraints and minimum mean. Selection/targets/config were committed and hash-locked BEFORE final evaluation. Only the selected method, matched probability control and previous frozen probability control were evaluated on final. Historical control17/29initializations are paired31→17,43→29 for diagnostics; only the newly matched control is the formal experimental baseline.

## Locked final (28contexts/model)

|method|mean NC BB|worst NC BB|vs3bet mean / worst|vs4bet mean / worst|
|---|---:|---:|---|---|
|previous_frozen_probability|0.703352162|3.053405532|0.822303592 / 3.053405532|0.584400732 / 1.153845693|
|probability_knn9|0.951012749|6.589049507|0.598209020 / 1.682641546|1.303816478 / 6.589049507|
|response_4096|0.005778591|0.032241192|0.007891537 / 0.032241192|0.003665646 / 0.008136443|

Mean reductions on SAME new cases: {"previous_frozen_probability": 99.17842131018853, "probability_knn9": 99.39237497233175}.

The newly retrained probability control itself regressed vs the previous frozen model; include both, do not inflate improvement by hiding that control regression. Prior reported0.643154/1.716479BB used OTHER boards, not directly comparable. Same-new-cases previous frozen model is0.703352/3.053406BB.

All5preregistered research criteria PASS:≥20%mean reduction; global worst nonincrease; vs3bet mean AND worst noninferiority; vs4bet same; absolute worst≤0.1BB. All28selected contexts below0.1BB. Selected worst positive-external-regret bound0.032241192BB agrees with restrictedNashConv; this is a limited-game convergence certificate, NOT real-poker exploitability. No final-based reselection/global refit. Local solving at final inference uses exactly the locked4096steps; this was declared before final. CI replay is deterministic verification, not another model selection.

## Structural comparison

|structure|response mean / max|matched probability mean / max|previous frozen mean / max|
|---|---|---|---|
|monotone|0.003570087 / 0.003780509|0.694705060 / 0.792010114|0.579198129 / 0.765731249|
|paired_rainbow_high|0.008237312 / 0.009307208|4.123184978 / 6.589049507|0.839196645 / 1.090455338|
|paired_rainbow_low|0.019593591 / 0.032241192|0.194794746 / 0.295302661|2.083725388 / 3.053405532|
|paired_twotone|0.000843885 / 0.001204742|0.194405998 / 0.233514526|0.176638216 / 0.205872013|
|rainbow|0.002480832 / 0.004139968|0.533895224 / 0.617431826|0.554084774 / 0.734223372|
|twotone_connected|0.002233227 / 0.003844194|0.519605267 / 0.646011315|0.231889574 / 0.233698676|
|twotone_disconnected|0.003491207 / 0.004644907|0.396497968 / 0.592414415|0.458732408 / 0.688302347|

## Prediction error, numerical accuracy, model error

Conditional target transfer MAE against the fixed matched probability-control opponent:validation1.517631BB/max21.087585;final1.547539BB/max30.480298. This is MODEL/OPPONENT-TRANSFER error, not numerical or sampling error, and not external GTO deviation. Final response uses actual current-board game values, not these inaccurate transferred EV labels. The selected method's success does not mean target prediction became accurate.

Full enumeration gives sampling error0 for FIXED board/policy/game; numeric guard1e-7BB. Initialization differences are not confidence intervals. Finite board results do not establish population-wide guarantees. Model misses later-street strategic betting, omitted actions and real-board chance integration. Real-game approximation remains UNKNOWN; no matching external GTO comparison. Formal acceptances0/12unchanged, regularGTO ranges added0. Existing research8×169=1352rows,HU1BB and2..9regressions maintained.

## Observed computation cost (validation only, independent readonly check)

14validation contexts, initialization31, one observed run. Every benchmark metric matched the frozen validation result at1e-12. No fit/selection/final access. Median/max seconds:

- full_hole_runout_matrix_seconds_shared_between_stages: 1.007258 / 1.041789
- features_and_game_seconds: 0.272522 / 0.337736
- cold_neighbor_probability_prediction_seconds: 0.687917 / 1.007855
- selected_planning_and_exact_certification_seconds: 0.142576 / 0.301368

The ~1.0second matrix is shared by both stage evaluations. Geometry is cold per benchmark context; timing is not smartphone or cross-hardware evidence. Response timing INCLUDES exact Python certificate computation; no claim it is native-only speed. Timing artifacts are observed receipts, not compared byte-for-byte in CI. Numeric/identity artifacts are verified separately.

## Tests, evidence and restart

Local command `python -B -m unittest tests.test_value_response -v`:14PASS. Includes analytic posterior/sign/zero-sum checks, an independent Python update comparison, exact replay, first-prior preservation, missing/nonfinite guards, private-information-only inference and stage-wise selection. Original modules and research data hashes are in dependency-manifest. Active GTO workflow retains11reached-range+14factorialtests and adds14newtests, selection/final replay at1e-12, plus a readonly validation benchmark smoke check. Final CI result is recorded in PR/receipt after the result commit; do not mark SUCCESS until actually completed. Aggregate PASS remains UNKNOWN if logs time out; no guessed sums.

```sh
python -B -m unittest tests.test_value_response -v
python -B -m gto.abstract.value_study --phase select --build-dir /tmp/value-select --output /tmp/value-select.json
python -B -m gto.abstract.verify_export --actual /tmp/value-select.json --expected docs/qa/value-response-20261104/selection.json
python -B -m gto.abstract.value_study --phase final --build-dir /tmp/value-final --output /tmp/value-final.json
python -B -m gto.abstract.verify_export --actual /tmp/value-final.json --expected docs/qa/value-response-20261104/final-results.json
python -B -m gto.abstract.value_benchmark --build-dir /tmp/value-bench --limit 1 --output /tmp/value-bench.json
```
Use a fresh output path; original evidence cannot be overwritten by CLI. Next study must exclude142used suit-orbits and preregister new splits. Next implementation: cached/continuous own-information conditional utilities and cheaper bounded local inference; measure discretization/continuation-model sensitivity and true-board-chance weighting in an independent research interface. Do NOT connect to frozen original CFR or alter8ranges/demo. Formal20stack/size original specs, external references and real-game approximation accuracy remain BLOCKERS. No fees/prod/main/otherPR/SSO changes. Draft remains. AUTO-RESUME/independent restart absent.

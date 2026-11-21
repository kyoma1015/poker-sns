# Preregistered public/own-feature generalization study

Base2b2f88f9. Original CFR, prior models,8research ranges and static demo unchanged.
Protocol was committed locally BEFORE feature implementation/validation. Selection
was committed separately BEFORE final computation. Ordered commits are published
in one ref update to avoid repeatedly starting unchanged CI.

## Fixed experiment
18training/6validation/6final boards,6structure strata, seeds1103/2203/3301.
Suit-orbit overlap and all previous6boards excluded. Model initialization17/29.
Teachers5000sweeps/board; retrained coarse100000sweeps on equal18board mixture.
Full card-removal/turn-river evaluation; chosen board weights are RESEARCH
weights,not actual flop chance. Macro mean averages conditional per-board NC,
not a claim of whole-poker exploitability or generalization to all flops.

Features: legacy own/public signals; pair structure,suit multiplicity,straight
connectivity,rank coordinates,SPR/position,made5category,pair-vs-board,overcards,
straight draws,nut-flush relation,hole high-rank bin,and binned own equity vs
ALL uniformly unknown compatible opponents. This last feature is
sum_j(2wins_ij+ties_ij)/(1980*1081),using ALL legal j,not the dealt opponent.
There is no opponent private-card input to the decision policy. SPR/position
are validated only at the existing two HU50BB contexts,not new stacks.

Every model is evaluated in the SAME richer information partition and4plan
action menu. Coarse models map to prefix signals; BR has the same richer own
signal for every comparator. Previous coarse-game NC range0.398..3.048BB used
different boards/information and is NOT a directly comparable numeric baseline.

## Validation-only selection
Seven candidates fixed before execution. Minimum mean validation NC across
boards/stages/seeds chooses one global configuration; fixed order breaks ties.
No final outcomes/boards are evaluated for this choice.
Selected: knn9_private8_board0.5.
|candidate|validation mean NC BB|worst BB|
|---|---:|---:|
|retrained_coarse|2.420913209|4.187177033|
|knn1_private1_board0.25|1.351882471|6.869347863|
|knn1_private1_board1|1.348038216|6.869312184|
|knn3_private4_board0.25|1.415998590|6.809837128|
|knn3_private4_board1|1.401220889|6.995910732|
|knn5_private4_board1|1.386277702|5.597101541|
|knn9_private8_board0.5|1.203344937|4.532968948|

Selection worst-case risk was known and preserved before final: objective was
predeclared mean,not a later override to optimize final/worst performance.
selection-lock.json pins protocol/feature source/selection bytes. Final phase
has no fit/solve/reselection. CI may reproduce deterministic results only.

## Same frozen STUDENT: train/validation/final
Post-lock audit evaluates the actual nearest-neighbor student on train boards,
not teacher loss used as a substitute for student training performance.
|split|contexts/stage-seed count|selected mean NC|coarse mean NC|selected worst|coarse worst|
|---|---:|---:|---:|---:|---:|
|train|72|0.009425077|1.871309693|0.028919048|3.684195751|
|validation|24|1.203344937|2.420913209|4.532968948|4.187177033|
|final|24|0.847890988|1.852747222|1.285742859|3.586962355|

Final mean reduction 54.236014% =1-0.8478909879079398/1.8527472215024847.
All final6boards*2stages*2seeds=24contexts per model,3models incl prior frozen.
|stage|method|final mean NC BB|final worst NC BB|
|---|---|---:|---:|
|vs_3bet|selected|0.781451107|1.285742859|
|vs_3bet|retrained_coarse|1.687738059|3.434188711|
|vs_3bet|previous_frozen|4.426612011|9.342048524|
|vs_4bet|selected|0.914330869|1.207316992|
|vs_4bet|retrained_coarse|2.017756384|3.586962355|
|vs_4bet|previous_frozen|2.771944543|3.587546885|

Predeclared final acceptance:
- >=20%mean reduction vs retrained coarse: PASS.
- worst NC must not increase: PASS.
- absolute worst NC<=0.1BB: FAIL.
Overall research acceptance FAIL; formal PokerID acceptance0/12 unchanged.
Sampling error0 on specified boards; numerical guard1e-7BB,not a statistical CI.
NC/2 is restricted exploitability,NOT actual NLHE exploitability.
External GTO comparison NOT PERFORMED; real-game approximation UNKNOWN.

## Residual problem,not hidden by selection
Teacher max train NC 0.028892826901103064BB.
Student train mean~.0094BB vs validation~1.2033/final~.8479BB. Transfer error
dominates the remaining teacher convergence error. KNN/private-feature
quantization and uniform-opponent strength vs actual reached ranges are plausible
causes,NOT causal conclusions. Validation worst-case degradation was recorded
BEFORE final. No source/weights/hyperparameters were changed after final.
Any next model changes need a NEW preregistered untouched final set; these6
boards cannot be reused as an untouched model-selection test.

Fixed6opponents (uniform,4pure plans,own strength),both seats stored for each
selected and baseline final context. Their BR gains are distinct from selfplay
NC. No artificial unit-oracle values are used as empirical policy results.

## Reproduce
python -B -m unittest tests.test_generalization -v
python -B -m gto.abstract.generalization_study --phase select --build-dir /tmp/select --output /tmp/select.json
python -B -m gto.abstract.verify_export --actual /tmp/select.json --expected docs/qa/generalization-20261101/selection.json
python -B -m gto.abstract.generalization_study --phase final --selection docs/qa/generalization-20261101/selection.json --build-dir /tmp/final --output /tmp/final.json
python -B -m gto.abstract.generalization_audit --selection docs/qa/generalization-20261101/selection.json --build-dir /tmp/audit --output /tmp/audit.json
Strict1e-12+source/protocol/selection identities; dependency-manifest pins old
unchanged engine and frozen inputs. No existing CFR hook/new normalGTO range.

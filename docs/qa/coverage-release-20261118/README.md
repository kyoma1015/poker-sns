# A/B release gate — verified app strategies remain0

Source085a3b3785fe8687ce0d74b118544c4020543d62; Open/Draft and8CI familiesSUCCESS
observed read-only. All old checkpoints/8BLOCKED candidates are protected.
**Formal acceptance0/12, verified RFI0/3bet0. No registry/search admission.**
The substantive advance is B's independently measured elimination of the specific
SB immediate-fold weakness, not a new claim of full native GTO qualification.

## A: compute-separated full-game coverage

New CoverageSolver reuses corrected average/first-external/native betting:
- Immutable169class chance batches: one physical combo perclass, other cards
  sampled without replacement; both policies frozen for the WHOLE batch. Multiply
  both regret and average increments by169*combo_mass. They are weighted frozen
  draws, not169 sequentially adapted CFR iterations.
- Adaptive per-pair chance law: q=.2*true class mass+.8*uncovered-root priority,
  then inverse-sqrt visit priority. q is chosen BEFORE cards; multiply CF/average
  by true_mass/q. Chance ratio<=5 follows from positive q, not numerical clipping.
  This does not bound all subsequent action importance products.
- Action-family prior: equal probability of legal fold/call/raise families,
  uniform within legal raise sizes. Every legal action remains positive. Only
  zero-mass rows change; no fold completion or hidden/future-card input.

Same seed17118101, identical warm source, target12sec PURE learning perarm.
Snapshot/deepcopy/serialization/compression/IO timed separately; complete atomic
unit slightoverrun. All study compute stays within300sec cap, storage<100MiB.

| arm | learning sec | checkpoint sec | paired worlds | rootS classes | R/S revisit |
|---|---:|---:|---:|---:|---|
| raw OS |12.0012|50.4652|5509|169|32.87% /32.24%|
| frozen class-batch OS |12.0132|52.0734|5746|169|32.72% /32.26%|
| adaptive first-external |12.0119|3.9963|122|169|1.52% /13.36%|
| adaptive first-external +family |12.0347|4.2421|130|169|1.39% /13.17%|

Source rootS145/169 (89.2911%card mass); all4now169/169 (100%). Counters describe
new stages, not inherited lifetime updates. Enumeration expands many distinct
continuations; its global revisit rate is still LOW. More observed root coverage
is not a quality certificate. Raw/batch OS also show no meaningful EV improvement.

The old gzip9 writer was measured during learning. Its executed runner is preserved
as training-source-used.txt. After learning, fast_checkpoint.py adds compact gzip1,
fsync and atomic replace; no strategy/retraining changes. Same final rawOS payload:
legacy1.917982sec/2,208,519bytes vsfast0.485927sec/3,031,962bytes, exact decoded
state equality. This single benchmark observed~3.95x faster saving at37%morebytes;
it is not a measured rerun of full-training IO costs. Future runner uses fast save.
Existing legacy snapshot bytes and source files remain unchanged.

## Fresh independent native comparison

Seven frozen profiles x16384common deal/action streams =114688actual native State
paths,63.3159sec, seed17118102.13simultaneous bounded empirical-Bernstein intervals
(7means+6source contrasts), family99.9%. No training on holdout outcomes.

| profile | SB EV BB | native untrained-S path rate | EV change fromsource / interval |
|---|---:|---:|---|
| frozen source |-3.499420|98.9685%|reference|
| prior-family only |-2.953705|98.9685%|+.545715 [-.876530,1.967961]|
| raw OS |-3.686493|93.2556%|-.187073 [-1.439141,1.064995]|
| batch OS |-3.330261|93.6707%|+.169159 [-1.079044,1.417362]|
| adaptive external |-3.476074|88.3301%|+.023346 [-.713687,.760379]|
| adaptive external family |-3.118286|78.2654%|+.381134 [-1.048786,1.811054]|
| B reduced preflop |-.125336|N/A|+3.374084 [1.793749,4.954420]|

Prior historical source rate99.1333%; same-holdout source98.9685%. A reduces
observed untrained path rate by20.7031percentage points in this holdout, but no
A EV contrast is significant. Path rate also depends on policy reach, not just
number of trained states. Do not report B's rows={} as zero/100%untrained: B maps
abstract preflop infosets and has an explicit postflop controller, a different
coverage concept. All A stage gates failed; no A expansion.

B digest bd46861da4c8c4eb786602315056092c5d253fd3d449b5183b01b96c5b2cc8f4.
B fold-deviation gain interval **[-.725361,-.023967]BB**, compared with source
[1.545744,4.453097] in this same holdout. This rules out immediate-SB-fold as an
improving deviation for B under this confidence design. The old source lower
2.038686BB and old paired delta-.022400[-.551464,.506664] remain preserved;
different sample/family allocations cannot be compared by lower-bound subtraction.
**No complete native BR upper/NashConv point or upper is measured for B.**
Changing from a refuted fold deviation to a non-improving fold does not prove
unrestricted exploitability decreased. Continuation/omitted-action bounds UNKNOWN.

## B all169/action follow-up and release decision

B alone passed the predeclared native stage gate; evaluate with unchanged existing
conditional evaluator, fresh17118103,4worlds/class,90sec cap; actual25.3020sec.
- RFI EV-.213026BB, interval[-13.477397,13.051345], width26.528742BB.
- vs3BBopen EV-.452264BB, interval[-13.722134,12.817605].
- Maximum actionEV interval width100BB; means98.484848/98.387097BB.
- First-decision pure-response estimates have wide intervals including0; they
  are not a full BR measurement. No accuracy PASS.

The prior26.528742BB width has NOT been reduced. B's native profile-only EV
interval width~.701394BB is a different measurement/allocation and cannot replace
all169/action precision. Real-game BR/NC upper, omitted-size and continuation
optimization error stay UNKNOWN. B's sampled abstraction NashConv.126800BB is
explicitly a different game, not comparable with old frozen abstract.932107BB.

B-all169-raw.json.gz preserves original evaluator output. Annotated B-all169.json.gz
clarifies that no runtime payoff surrogate is used, while training abstraction
error is UNKNOWN; generic zero runtime-surrogate error is NOT zero GTO/model error.
Numeric EV samples are unchanged. No further training after precisionfailure.

Fastest IMPLEMENTED early route is existing Betting/card-removal/CFR abstraction,
with4.44sec generation and four169-row exports. But verified strategy count0
means this cannot ship as normal GTO. See sibling release-route-20261118 README
for primary-license comparison and unresolved mathematical work. Four checked OSS
sources supplied no verified applicable HU50 strategy dataset; no commercial chart
or new external engine code was imported. Permissive code rights do not certify
strategy data, applicability or accuracy.

## Integration, tests and handoff

Existing certificate/registry/search admission remains unchanged. B's research
export is registry_ready=false and tagged PENDING_FORMAL_SPEC_APPROVAL. Formal
20stack/all-size/MTT/ring/ante/rake profiles and quality proposal are not adopted.
All formal12conditions remain mandatory; no partial formalPASS or new normal rows.

New A9tests PASS and B5tests PASS (focused logs, no manual oldQA/successCI reruns).
A tests cover independent frozen CF/average/chance oracle, exact removal, adaptive
mass/q, all-positive priors, interrupted-batch nonpublication, RNG/priority resume
and deterministic lossless atomic save. B tests cover actual native legality,
all169rows, unknown3.5BB response, postflop information constraint and blockers.
Qualification automaticCI adds both modules to prior53 (67configured tests).
No TS/UI changes; local npm build/lint/browser not repeated. CI is not GTO quality.

Manual A restore: coverage_study.load_model(rules,native,checkpoint_path).
Load B: preflop_release_solver.load_policy(build_dir,strategy_path). B stores a
frozen strategy/kernel, not resumable C++ R/S; deterministic generation may be
rerun, but no automatic restart exists. A's complete R/S/RNG/prior/priority states
are resumable. Old source checkpoint and all research history remain intact.

Next release-critical work: range-conditioned postflop continuation and quantified
omitted-size/native deviation error; independent BR upper and all169/actionEV
precision for ONE frozen B digest; approved formal profiles, then existing
certificate->registry->search acceptance. Do not spend longer on failed A arms or
substitute sampled abstraction convergence for true-game quality. No production,
DB/Storage, main, deploy, SSO, billing or destructive operations were performed.

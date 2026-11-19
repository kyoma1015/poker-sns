# Fullstreet joint CFR+ — research gate, first release still BLOCKED

Base ac72bafd5d42a9c75f88eb28a86aec3de362466d, Draft PR120. Full first-release12
conditions remain unchanged:2–9 players including6max/9max, multiple approved
stacks, positions,169 frequencies/EV, RFI+3bet and possible4bet, ante/rake and
unequal stacks. HU50 is ONLY an isolated research milestone. Formal0/12;
verifiedRFI0/3bet0, legacy8BLOCKED_UNVERIFIED, no ordinaryregistry/search admission.
No pending20-stack/size/MTT-ring/ante-rake concrete values were adopted.

## What changed and what is actually solved

New fullstreet_solver.py/fullstreet_core.cc jointly optimize preflop/flop/turn/
river in ONE fixed finite imperfect-information game, alternating CFR+, linear
realization averaging. No frozen old-range payoff/new-range resolver switch.
884 native legal public-tree nodes; native3/10/50 preflop, check/halfpot/jam on
all3postflop streets, not all possible sizes. Current public paired-prefix and
own169+revealed flop/turn made/fourflush/straight features+river absolute-nuts
features key the policy. Future public/private suffixes are integrated BEFORE
BR maximization or regret update. Neither actual opponent cards nor future
board is passed into the acting policy. Counterfactual vector terminal payoff
uses private-pair joint chance, not independent ranges. Policy.posterior computes
same-policy Bayes range with own/public blockers and action likelihoods; no
separate runtime optimization changes the fixed policy.

Per sampled complete board, all1081 physical private pairs and all1,070,190
compatible ordered pairings are enumerated exactly. Showdown uses original fast
rank, independently checked against NativeState rank7. Board strata000/001/011/
111 have combinatorial marginal weights. One representative board per stratum
is a SMALL QUADRATURE MODEL, NOT an unbiased exact full-deck solver. Public-board,
private-feature and omitted-size error bounds remain UNKNOWN. Abstract perfect
recall retains all previously observed feature/public bits and public history.
Actual hole-card identity is abstracted; its lost-information error is UNKNOWN.

Parent actual R/S checkpoints are hash-bound/read-only and average-policy arrays
are revalidated. Since the game changed, inherit average behavior only; fresh
R=1e-15*float32prior, S=0, inherited_regret_epochs=0. The nuts prior is explicitly
own/public legal behavior, not learned quality. At zero-average known rows use
this declared prior; unknown preflop histories use protected complete-A fallback,
unknown postflop histories check/call or river absolute-nuts maxraise if legal.
No missing-history fold completion. These fallback effects remain in native tests.

## Exact oracle gate

fullstreet_oracle.py independently enumerates all pure infoset BR policies and
path-product CF reach/regret/realization average. Three tiny games, including
future-public/private suffix hidden until river:1024-step complete NC respectively
0.000040993380802,0.000035745019318,0.000019462996038 BB. All3 decrease from64/
256steps; profile/BR/gradient/average/denominator agree within1e-12. This is proof
for these finite tiny games ONLY. Tests also check native all884nodes and every
selected terminal win/loss/tie, blockers, normalization, legal short-all-in and
same-policy Bayes range. Tiny checkpoint continuation is bit-exact.

## HU50 bounded pilots and stop decision

Two seeds17120101/17120102,4trainboards each;180sec/seed,512MiB estimated working,
200MiB QA disk cap. Predeclared pilot points0/16/64/128 were completed; no256
expansion. Timing excludes initial moment construction but includes pilot
measurement/checkpoint exports. Actual84.745/100.981sec; recorded peakRSS
505,368,576bytes (~482MiB). Actual QA disk usage is separately recorded below.

| seed | train NC16→128 BB | old joint same-fullstreet fresh NC | fresh NC16→64→128 BB |
|---|---|---|---|
|17120101|2.074763→0.181211|21.391449|14.507823→15.470511→15.815748|
|17120102|2.171752→0.217574|22.025238|10.296256→11.167176→12.055255|

Fresh boards share no train/old-heldout flops. After the fixed pilot, earliest16
was selected by this validation curve; therefore fresh_heldout is VALIDATION
for this selection, NOT independent final evidence. selected-checkpoint/policy
are deterministic16-step reconstructions, trainNC equality checked; final128
checkpoint/policy remain preserved. Do not present16 as a preselected winner.
Previous flop-only NC3.464242/5.029725 is a DIFFERENT game and is not a valid
before/after comparator. Fullstreet same-game improvement exists in this small
model; the train-validation gap and worsening16→128 reject blind longer training.

RFI/vs-open/vs3bet all169hands ×2 selected policies genuinely reoptimized and
exported with all native-selected actions, normalized frequencies, positive
realization mass and train/validation conditional MODEL actionEV. These EVs
have no native per-hand confidence intervals; native_action_EV_interval=null.
No zero model value is an assertion of native EV precision. Full169/all-native-
action EV intervals/precision remain UNKNOWN; root selfplay CI is not that metric.

## Independent native gate

native.json/native-checkpoint.json.gz: new seed17120201,2048complete-deal worlds,
13profiles/probes=26,624 native paths,5.460sec. Shared per-world random tape,
source/native binary/policy digests and full worlds retained. All21 intervals use
bounded empirical-Bernstein with family99.9% union allocation, NOT normal CI.

| selected policy | native SB EV BB [family interval] | paired change vs oldB | vs current joint |
|---|---|---|---|
|seed1|+0.013184 [-2.254813,2.281180]|+0.229248 [-3.295874,3.754370]|+0.270752 [-3.423570,3.965074]|
|seed2|-0.105713 [-2.178017,1.966591]|+0.110352 [-3.310870,3.531573]|+0.151855 [-3.485502,3.789213]|

NO significant native EV improvement. Root CI widths4.535992/4.144608BB are not
per169/action precision. Seed1 legal-deviation gains:3.5open+2.184082
[-3.805339,8.173503],10.5threebet+0.888184[-3.785014,5.561381],riverjam+0.464844
[-3.026646,3.956334],immediatefold-0.513184[-3.994630,2.968263]BB. Additional
2.5open+2.173340 and9threebet+0.851807 likewise inconclusive. These wide intervals
are NOT robustness passes or complete BR bounds. River-nuts probe oldjoint gain
+0.113281 vs new0; reductionCI[-2.547359,2.773921] is inconclusive. New nuts probe
3jams/201queries, old5/561. Previous monotone-nuts positive lower bound does NOT
transfer to the changed defender; no zero-gap/solved claim.

Complete nativeBR upper, nativeNC point/upper, full169/action precision,
uniform continuation error and omitted-size error: UNKNOWN. No physical100BB
bound substituted as convergence. Native quality gate NOT PASSED; no expansion,
certificate or ordinaryregistry admission.

## Coverage: support is not confidence

Selected16 repeated full-CF sweeps; every CF-supported row was revisited (100%).
Dense allocated includes unreachable/physically impossible feature combinations,
so allocated fraction is a diagnostic, not exact whole-game population coverage.

|seed|turn CF visited / allocated|river CF visited / allocated|river positive average|
|---|---|---|---|
|1|58,860/243,360|191,516/2,747,264|179,083|
|2|63,450/243,360|212,344/2,747,264|198,724|

Full preflop support1,352/1,352 abstractrows each; selected3contexts169/169each.
Old heldout flop signals absent from new train decrease78→15 and55→2, measured
on the same old heldout support. On disjoint native selfplay, worlds touching
any zero-average row:192/2048=9.375% and97/2048=4.736328%; zero off-tree selfplay.
Turn zero-average queries204/628=32.484076% and87/452=19.247788%; river231/433=
53.348730% and115/273=42.124542%. Thus unseen continuation remains substantial.
Previous A99.13% is a DIFFERENT solver/evaluation cohort, not a paired rate gain.
No previous fullstreet rate exists for direct before/after. The unlearned prior
is explicit and counted, never claimed trained or verified.

## 6max / 9max and full release

See MULTIPLAYER.md and multiplayer-evidence.json. Minimal offline all-seat profile
adapter binds full rules/provider digest, causal own/public observations, native
alllegal sizes and full52deck. Six regressions prove independent6/9 unequal-stack
sidepot/refund/rake/ante vectors and no-flop-no-drop; missing policy fails, no
HU array padding or pairwise-equity equilibrium claim. Existing2..9 EV engines
reused. No6/9 trained/verified policy; multiway joint chance/N-owner regret and
independent unilateral BR/error oracle remain blockers. General multiplayer/
raked games do not inherit HU zero-sum convergence guarantees.

## Reproduce / resume without repeating old long studies

114 regressions PASS,18.349sec; regression.txt and CI workflow contain exact
module list. Build native/range per existing workflow; build new helper:
`python -B -c "from gto.qualification.fullstreet_solver import build; build('/tmp/fullstreet-build')"`.
Exact gate: `fullstreet_solver.study_exact(lib,target)`; no need rerun savedpilot.
Actual HU16 R/S was restored twice sequentially, one additional step: hashes bit
identical, originalcheckpoint unchanged, receipt hu-resume.json. No automatic
resume service exists. Restore selected or final R/A/visits/t via Game.restore,
load its train.npz and reconstruct prior from policy-initial.npz['pi'] as float32;
verify checkpoint/meta/source/board hashes first. Game layout from corresponding
policy json. Old preflop/flop regret history must not be spliced into this game.

Build hash strict: archived policies require the recorded source/helperbinary;
compiled .so files remain local/tmp, NOT inGit. Recompilation on another compiler
may change binaryhash: strict archived evaluator then REJECTS. R/S plus moments
still resume explicitly; re-export under truthful new buildhash/new digest, and
redo required new-build validation before comparing. Do not rewrite old evidence
or claim portable binary equality. selected-checkpoint16 and checkpoint128 both
preserved. Native checkpoint has completed2048values/worlds; no auto-resume claim.

Original Git qualification/research checkpoints recovered. Inaccessible old
external SQLite/cache/recovery-ZIP bytes remain NOT recovered. Existing frozen
CFR/HU1BB/2..9/native engines/oldQA protected. No UI/npm localbuild/browser QA:
Python/C++ qualification-only changes. All required newCI still must be checked.
No productionDB/Storage/main/Vercel/SSO/billing/destructive/manualSUCCESS-CI action.

Next: improve board/private abstraction generalization and zero-average turn/
river support with small independent gates before more iterations; then full
nativeBR/error and169/action precision, multiway joint solver and approved formal
profiles. Formal20stack list, legal-size products,MTT/ring,ante/rake/ICM concrete
choices remain owner decisions under existing proposalA/B/C, all PENDING.

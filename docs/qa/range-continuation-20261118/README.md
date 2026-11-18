# Internal range-conditioned continuation — release BLOCKED, verified strategies0

Source76d8a9cec17d1ef9cc6dadeb423b4f99dfafee5e. PR120 Open/Draft, source8CI families
SUCCESS verified read-only. Existing A, B,8BLOCKED candidates and all old evidence
are unchanged. No postflop UI, app route, DB, registry or search catalog addition.
**Formal0/12, verified RFI0/3bet0. No condition relaxed or formal profile adopted.**

## Implemented continuation and its exact scope

Preflop frequencies remain frozen B (bd46861d...). This isolates continuation
changes. New RangePolicy uses only own hole, current public board and full public
action ledger. All possible private2card combinations are hypotheses; actual
opponent cards and actual future board are never supplied to the provider.

- Start from uniform physical holes; replay B preflop action likelihoods.
- Public beliefs are factorized realization weights, NOT independent actual
  hole draws. At current board, exact disjoint-card pair mass r0[h0]*r1[h1] is
  counted over compatible1326x1326 combos, excluding every overlap/board card.
  Conditioning on own hole removes its blockers and normalizes opponent mass.
- Public postflop actions multiply acting-range weights by the published policy's
  likelihood. Earlier actions use only the board visible THEN; future cards are
  filtered only when revealed. Relative per-player normalization preserves joint
  conditional law. Zero-reach preflop histories use explicitly uninformative
  off-path beliefs, not an inferred fold or nearest-size mapping.
- A deterministic one-street CFR solve uses8current-rank buckets/32iterations,
  native-legal check/halfpot/jam and fold/call responses. Modeled child histories
  reuse their original street plan, even after cache eviction. Unknown legal
  sizes create a fresh exact-ledger subgame.1%uniform legal tremble gives positive
  postflop likelihood to every legal action; no clipping of regret/importance.
- Current5/6/7card ranks are used. Flop/turn draws and later strategic choices are
  approximated; this is NOT a full multistreet equilibrium. Private-bucket,
  horizon/continuation and omitted-action errors all remain UNKNOWN.

The native game still deals all actual streets and settles actual terminal ranks;
only the acting strategy uses this internal approximation. No call is treated as
free terminal showdown in native evaluation. The existing B preflop chart was NOT
reoptimized against this continuation: EV precision is currently insufficient.
The new model is connected to preflop EV evaluation, not published as a feature.
Old B actionEV/certificates must not be relabelled with the new policy digest.

Final selected8bucket digest:
**f290ba1f24d9fb27fc7a8291d507ce892effe1ca0260d1e83194a0b2f32acd6f**.
It binds source, config, preflop B and actual compiled kernel hash. Frozen config
and build/toolchain metadata are saved. A changed binary/source/path identity
requires a new digest/evaluation; do not silently reuse these measurements.

## Correctness regressions and a validation-found defect

Nine controller tests PASS: exact blocker/joint bucket mass versus independent
Python enumeration on flop/turn/river; conditional preflop and post-action Bayes
likelihoods; normalized all-legal probabilities; exact unknown sizing; true short
all-in; cache order/future-board noninterference; unchanged all169preflop rows.
Native State independently verifies normalized raise-to-one action3, whose public
history uses marker-3 (distinguishing check/call1). The NEW replay initially missed
this marker; additional size probing caught it. Minimal decoder fix added, old
engines untouched. Final native conditional cohort replay had identical numerical
gains on normal histories, with the final digest. Failed seed17118203 is debugging
data, not heldout quality evidence; subsequent probes use fresh17118205.

pre-fix-source-reconstructed.txt is an inverse-patch reconstruction, verified
against the pre-fix policy digest; it is NOT a claimed recovered original ZIP.
Pre-fix pilot/results are preserved as such, never used as final-policy admission.
Two sampler tests PASS: partial EV/RNG resume and conditional sample/RNG/counter
resume exactly match uninterrupted runs with a finite payoff oracle. No old
successful QA/CI was manually rerun. New automatic qualification adds11 to70
(81configured tests); CI results are recorded in PR120.

## Known river deviation — significant root reduction, not full BR proof

The original B receipt has8192worlds,56nuts-action events (including ties),55
positive gains, native BR/NashConv LOWER0.170583BB. Preserve it unchanged.
Replaying all8192heavy new-policy paths is unnecessary: preflop is unchanged, and
any new river nuts deviation can act only on the same deal/preflop event E. Outside
E both policies with/without this deviation are identical, so payoff difference0.

Use old fixed56/8192 count for P(E), NOT inverse-binomial rejection attempts.
Fresh IID rejection samples are selected solely by OLD B's event, never by new
payoffs. Conditional old-new difference D lies[-100,149]BB (oldgain[0,49], newgain
[-100,100]). Root reduction=P(E)*E[D|E]. Exact-binomial mass lower and conditional
Hoeffding lower yield the stated family99.9% bound. This is stratified independent
native evaluation under the SAME root distribution, not information leaked into
policy or an easy-only win selection. Tied oldnuts events are included.

Original fixed-pot guard256events: both8/16bucket variants pass; after decoderfix,
actual native replay of the fixed cohort gives identical gains.8bucket root
reduction lower0.059820BB;16bucket0.059633BB. Choose lighter default8, no parameter
fitting to hidden hands. Its fixed-guard nuts actions fell17/256, so we additionally
checked ALLmatched river pots to avoid merely escaping the old guard.

**Generalized independent gate** seed17118206:512E-events,73926rejection draws,
70.668sec; new deviation may valuejam at ANYmatched river pot. For old passive B
this generalized event is identical to originalE. Newprovider uses own/public
cards only; all990possible opponent pairs checked when testing nuts.
- P(E) lower0.004228328 (source count56/8192).
- Conditional oldgain44.705078BB, newgain0.458984BB; old-new44.246094BB.
- Conditional reduction lower22.793394BB; ROOT reduction LOWER **0.096377951BB**.
- Confidence family99.9% (mass + reduction). New deviation acts125/512events.
- New root-gain POINT estimate(56/8192)*0.458984=about0.00314BB; absolute upper
  not obtained. Do not subtract two lower bounds or call this zero exploitability.

Reduction can include changed postflop reach and improved decisions; it does not
prove a river subgame equilibrium or a reduction in full native NashConv. All
preflop actions are unchanged, maintaining the support argument. Generalized
results belong to the final frozen digest, not the pre-decoder prototype.

## Independent new deviation probes and profile EV

Fresh seed17118205,256worlds/1536native paths,20.427sec; family99.9%5contrasts:
- BB river alwaysjam gain-.761719BB, interval[-20.239618,18.716180].
- BB flop halfpot gain+.552734BB,[-18.550867,19.656335].
- SB3.5BBopen gain+2.515625BB,[-24.442631,29.473881].
- BB10.5BB3bet gain-.517578BB,[-23.402398,22.367241].
No positive BR lower demonstrated, but all intervals are wide. In particular the
positive off-tree3.5BB point is unresolved risk, NOT evidence of all-size accuracy.
Finite probes cannot certify no new exploit or supply a complete BR upper.

Fresh fixed2048world comparison seed17118204,4096native paths,88.060sec:
old B SB EV-.170898BB [-1.658047,1.316250]; new+.240723 [-2.033298,2.514744].
Paired improvement **+.411621BB [-2.696276,3.519518]**, family99.9%3intervals.
Overall EV improvement is NOT statistically established. Prior B+3.374084BB
versus frozen CFR is separate historical evidence; do not compare point means
across different samples as a new performance proof. Profile-only EV interval
width4.548042BB is not all169/action precision.

## Preflop internal EV integration / all legal sizes

partial-canonical-action-EV.json:169classes each for forced3BB RFI and10BB BB3bet,
338native paths,9.785sec. Correct no-replacement chance and exact source-open
posterior, independent17118207. Actor-net EV includes blind payments. Aggregate
forced-action POINTs+.475113/-1.792520BB, not profileEV or independentBR.1sample/
class gives no useful precision interval; all rows are explicitly unverified.
This is ONLY2canonical actions, not all169/alllegalaction acceptance.

size-legality.json:534publicstates/1602private rows,7.215sec. Exhaustive legal
raise-to choices at RFI/vsopen/vs3bet prefixes and representative flop/turn/river
nodes match native legal sets; provider probabilities are legal/normalized.
This is legality, NOT an omitted-size error or EV bound.

Measured canonical throughput~.029sec/game implies a rough129792rollout all-action
pass far beyond90sec; omitted-size branches have different reaches, so estimate
is uncertain. No long complete run was launched. New digest full169/action EV
precision and omitted-size errors are **UNKNOWN**. Old B's26.528742BB width stays
historical baseline only; do not attach it to the new digest as a measurement.
Complete nativeBR upper, NashConv point/upper, uniform continuation/private-
abstraction error bounds remain UNKNOWN. No trivial100BB cap used as convergence.

## Release blockers, protection and manual resumption

Verified app strategies0; formal0/12 unchanged. This is an internal continuation
prototype, not a released strategy. No new ordinary registry/certificate/search
rows. No postflop UI or general public feature. Formal20stack, legal size/rake/
ante/MTT/ring decisions remain PENDING; isolated HU50 research adopts none.

Manual reconstruction:
1. Restore this commit under the source identity path and build original thin
   native module as before; build range library via range_continuation.build(dir).
2. range_continuation.load(native_build, old_B_strategy_path, range_library).
3. Verify policy_digest matches frozen-policy.json; otherwise evidence is not for
   this rebuilt policy. Caches are disposable memoization, not learned state.
4. range_followup --ev --resume native-EV-checkpoint.json resumes a partial fixed
   EV sampler. range_study --general --resume river checkpoint resumes conditional
   draws. Caps apply across resumed chunks. No automatic restart service exists.

Config is the frozen algorithmic policy, not exported global CFRR/S; each public
street solve is deterministic32iterations. Old A R/S and all B/kernel bytes stay
intact. Evaluation RNG/sample checkpoints, physical world lists and build hashes
are saved. Old checkpoint v1 diagnostic counters can be UNKNOWN on resume; sample
means/RNG remain preserved. No claim of inaccessible old researchDB/ZIP recovery.

Next release-critical work: stronger range-conditioned future-equity/multistreet
continuation with quantified abstraction error, sufficient EV accuracy before
preflop reoptimization, all-size independent deviations/completeBR upper and
all169/action precision; then approved formal profiles and unchanged certificate
->registry->search gates. Do not expand failed/inconclusive models into long
population training. No productionDB/Storage/main/deploy/SSO/billing/destructive
operation or successCI manual rerun occurred. No TS/UI changes; app local
npm build/lint/browser not repeated. CI is not a strategy-quality certificate.

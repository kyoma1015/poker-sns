# Fullstreet generalization and N-owner joint solver — quality still BLOCKED

**Latest: see CORRECTED SCHEDULE section below. Earlier transfer/ results are
HISTORICAL measurements. Their owner1 whole-schedule unbiasedness claim is
WITHDRAWN; legal-policy native measurements remain valid, but that schedule is
not adopted. Corrected first-worse gate retains seed1 original16 and improves
seed2 only. Both-seed adoption gate FAILS; no expanded learning or registry.**

Base509e2141012ceb4048abf33005b9a2b5a932e9c0. PR120 stays Open/Draft. Full first
release retains ALL12 requirements,2..9 including6/9 players, positions, multiple
stacks,169 frequencies/EV, RFI+3bet/possible4bet, ante/rake/unequalstacks. HU50 is
research only, not first-release completion. Formal0/12, verifiedRFI0/3bet0,
legacy8BLOCKED_UNVERIFIED unchanged. No ordinaryregistry/search/public writes.
No pending concrete20stack/size/MTT-ring/ante-rake/quality values were adopted.

## Cause identified, not another uncontrolled long run

cause.json reads ACTUAL original16/128 R/S checkpoints. Nonzero-CF-visit masks are
IDENTICAL in bothseeds: more repetitions of the same4boards add ZERO supported
action entries. Existing validation NC worsened16→128 despite lower training NC.
Different32-board pool demonstrates same abstract private/public signal AA vsKK
conditional showdown equity spanning0..1 within a paired-prefix stratum. The
current made/draw bit conflates different known board ranks/hand strengths; more
iterations cannot recover information removed from the policy key. This is a
measured aliasing example, NOT a fullpopulation uniform-error certificate.

## One existing solver, expanded board law, explicit warm initialization

Frozen fullstreet_solver.py/fullstreet_core.cc/884nodes/infoset map unchanged.
fullstreet_generalize.py/fullstreet_transfer.py reuse their exact CF update,
private-card removal, native legal sizes, accounting and causal feature prefixes.
32trainboards=8per000/001/011/111 stratum, distinct flops. At each sampled step,
stratum drawn with exact combinatorial weight, representative uniformly within
stratum, all1,070,190compatible physical private pairings integrated. Thus the
sampled gradient and realization-average contribution have the SAME expectation
as this finite32board game. Independent tiny path-product oracle checks this for
both owners and hiddenfuture features. No all-deck unbiased/fullgame claim.
Single-board BR is NEVER averaged as finalBR: evaluation joins allhidden future
worlds before maximizing, using protected fullstreet backend.

First fresh-R/S initialization failed16-step gate: selectionNC11.285283→12.450757
and11.962835→12.445400. Stopped BOTH immediately. Rejected evidence preserved at
root/seed, source snapshot fresh-driver.py, no final/native PASS inferred.
Within SAME sampling method, retain actual old16 R/A/visits/t as finite initial
state, old128 protected. This prefix was drawn from OLD4board game, NOT from the
expanded32board law; no unbiased-history or same-law-prefix claim. Its finite
warmstart influence/error is UNKNOWN for fullnative convergence. No reset/rewind
of old files. New selection and final board seeds were fixed BEFORE this trial;
failed fresh-R final data NOT reused. All current source hashes recorded.

## Real early stopping, selection/final separation

Seed offsets:+100000 train,+600000 selection,+700000 final,+400000 sampling.
4selectionboards and4finalboards have disjoint flops from train and old cohorts.
Targets+16/+32/+64/+128,90sec/seed,512MiB,200MiB QA cap. First nondecrease vsBEST
selection (not vsoldbaseline) stops further updates. Fresh-R pilot proves stop
at16. Transfer improves everypoint, so all128 additionalupdates completed; no256.
Final board values are computed ONLY AFTER best R/S and policy are written and
freeze.json records selection_finished/arrayhash. Final set used ONCE for
oldjoint/old16/old128/new same-finite-game comparisons, never for choosing steps.
It is independent of selection, but only a4board quadrature game, NOT statistical
population NC/complete-native upper. Do not recycle it as independent evidence
for the next development iteration. native seed17122201 similarly becomes prior
observed evidence after this report; next selected policy needs fresh final data.

|seed|selection initial→+128 NC BB|final oldjoint|final old16|final old128|final new|
|---|---|---|---|---|---|
|17120101|11.658358→5.686169|22.512320|14.200033|14.937535|4.158688|
|17120102|10.895836→6.123955|21.997516|13.377105|15.356105|6.023415|

Exact old128 values in transfer/seed/result.json. Different-board prior report3.464/5.030 or14.508/10.296
must not be compared directly. New final figures and old controls above use same
fullstreet game, chance law and original two seed policies.
All169 RFI/vs-open/vs3bet frequencies/action models exported for2new policies.
Model conditional actionEV is NOT a native per169/action CI; native intervals
remain null. Policy digest, source/build, checkpoint, finite chance boards and
original prefix identities retained. No certificates or normalregistry admission.

## Independent native gate —8192rootworlds,21profiles/probes

transfer/native.json and native-checkpoint.json.gz preserve full worlds, random
tapes, allper-profile values, unseen indicators/counters and policy digests.
Seed17122201, fixed8192worlds/172,032 native paths,40.320sec,90sec cap. 40-event
family99.9% bounded empirical-Bernstein intervals, CRN paired differences.
PeakRSS531,542,016bytes<512MiB. Average arrays in evaluator reduce to EXACT boolean
positive-support indicators after169 export; no probability/fallback or identity
change. This avoids keeping duplicate dense diagnostic floats.

|candidate|SB EV BB [99.9%family CI]|paired vs corresponding old16 BB|
|---|---|---|
|seed1|+.085510[-.844790,1.015811]|+.008972[-1.369528,1.387473]|
|seed2|+.030151[-.950937,1.011240]|-.141235[-1.549895,1.267425]|

Vs oldjoint +.226746[-1.114294,1.567785] and+.307312[-1.108027,1.722651]; vsoldB
+.153320/+.097961 likewise inconclusive. No significant nativeEV improvement.
Root EV CI widths1.860601/1.962177BB, corresponding old16 widths1.751447/1.602607
in SAME cohort. Precision did NOT improve relative to same-budget old16; smaller
width than old2048world report is largely more samples, not a variance proof.
No root CI is a full169/action confidence certificate.

|seed|old16 any-unlearned worlds|new|old16 turn query rate|new turn|old16 river query rate|new river|
|---|---|---|---|---|---|---|
|1|734/8192=8.959961%|64/8192=.781250%|753/2658=28.329571%|0/3878=0%|878/1836=47.821351%|79/1943=4.065878%|
|2|409/8192=4.992676%|65/8192=.793457%|379/1742=21.756602%|25/4370=.572082%|481/1089=44.168962%|80/2333=3.429061%|

Prior published baseline turn32.48/19.25%,river53.35/42.12%,any9.375/4.736% is
preserved (DIFFERENT2048world cohort). The table is proper paired8192 comparison.
Query rates are descriptive, variable path counts depend on each policy. IID
per-world binary unlearned differences ARE bounded paired observations. New-old
any-world rate99.9%familyCI seed1[-.103754,-.059820],seed2[-.060724,-.023261]; turn
[-.083511,-.044907]/[-.044445,-.012684],river[-.083107,-.042137]/[-.047962,-.013073].
All6upperends<0: significant reduction in paths touching unseen rows. Same-world
CRN does not force identical histories; this is eachpolicy selfplay-path coverage,
not coverage under a frozen opponent/public-history population. Bothselection
and independentnative coverage gates pass for retaining this method only. No
further learning scaled this task; full quality gates remain blocked.

CF visited turn old58,860/63,450→new87,660/87,210; river191,516/212,344→391,414/
380,492. River revisits99.2187%/99.7963%,turn100%/99.8968%; all preflop1,352rows.
Dense allocated includes physically impossible/unreachable combinations. CF
revisit/support count is not confidence or fullpopulation policy accuracy.

Legal gain point [CI] BB, newseed1/2:
-3.5open +1.366638[-1.061448,3.794724] /+1.421997[-1.007033,3.851027]
-10.5threebet +.824219[-.811686,2.460123] /+.655701[-.934451,2.245853]
-riverjam -.307495[-1.375503,.760513] /-.597290[-1.741244,.546664]
-rivernuts -.000854[-.681505,.679796] /-.000732[-.647427,.645962]
Immediatefold,2.5open,9threebet also measured, all inconclusive. Nuts point near0
is not solvedproof, and old monotone-nuts lower bound cannot be transferred to
changed river defenders. No attack1-only completion claim. FullnativeBR upper/
NCpoint/upper/all169EVprecision/uniform abstraction+continuation/omitted-size
errors all UNKNOWN; no trivial physical bound substituted.

## Multiplayer actual minimal joint learning

multiplayer_joint.py moves beyond supplied-policy replay: same finite native
hidden-information game builds ALL seat R/S and vector payoffs, N-owner
counterfactual regret/realization updates, best responses group hidden worlds
by actingseat own/public Observation beforemax. No HU array padding/product-HU
range shortcut. Leaf rake remains negative utility sum, not forced zero-sum.
Reuses offline adapter to replay learned profiles on native/reference settlement.
No native engine, sidepot semantics or existing6/9tests changed.

Restricted action game: fold or maxlegal all-in raise/all-in-call; ordinary
non-all-in calls and other sizes omitted. Two explicit correlated full52deck
worlds, not full-deck poker. Allactinginfosets preflop, no futureboard/opponent
cards supplied to provider. A first attempted broader call-tree hit the10,000node/30sec
budget gate and was stopped; final narrowgame is labelled, not treated as fullRFI.

3player independent exhaustive PURE POLICY BR (independent recursive path sum)
agrees per seat. 6/9 use SAME N-owner code, native unequal10/12/14chip stacks,
BBante2 and5%rake diagnostic rules, not formal adoptedprofiles.32joint updates:
3player sum restricted unilateral gains5.375→.009471BB (13nodes/11infosets);
6player1.781250→.001894BB (125/109);
9player23.070313→.044506BB (1021/893).
These are exact finite2world restricted-response gains, NOT fullnative NC or
multiplayer Nash proof. CFR+ has NO general multiplayer/general-sum convergence
guarantee; report measured unilateral gains only.6/9 checkpoints/profiles/R/S
saved. Missing offsupport profile row FAILS, never silently fills folds. No
169hand/multi-stack positional6/9data or certified strategy generated yet.

## Regression / checkpoint / recovery

121 tests PASS20.005sec, includes existing114 unchanged plus7 new expectation,
first-worse stop, train-selection-final split, independent pureBR, N-owner path
regret/average,6/9privacy/vector/native replay and exactR/S restore/identity tests.
Exact2type1024step NC.000040993/.000035745/.000019463 retained and rerun within
existing fullstreet regression. New chance expectation matches independent
oracle1e-12. Full test command is existing qualification workflow run plus
`gto.qualification.test_generalize`; regression.txt captures each result.

New focused exact command:
`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_generalize -v`
7PASS2.433sec. Fullsuite with QUALIFICATION_BUILD and RANGE_BUILD is CI's exact
module list; no fullapp/npm/browserQA because no TS/UI/product flow changes.

Actual two-seed transfer144 R/A/visits/t and samplingRNG were restored twice
sequentially, nextboard draw+oneupdate bit-identical; resume.json records hashes,
originalbytes unchanged. No automaticresume or externalservice capability.
Load corresponding policy-initial prior from OLDseed, current train-pool block,
Game.restore(transfer/seed/best-checkpoint.npz); totalepochs144 old16+new128.
Replay samplingseed+400000 choices with WEIGHTS and randint8 for each recorded
last-state.draws, verify drawsequence, then resume nextboard. Last==best144 here;
for a rejected laterstage, replay only until BESTadditionalstep, not laststep.
Helpers/binary and chance/config hashes must match. Compiled .so remainslocal/tmp;
othercompiler may changebinaryhash, strict evaluator rejects old identity. Re-export
truthfulnewbuild/newdigest and redo required checks, never rewrite old evidence.
Old R/S16/128, old8candidates,HU1BB,frozenCFR/2..9/oldQA untouched. Old external
DB/cache/recoveryZIP bytes remain inaccessible, NOT recovered. Own generated
Python caches only are removed beforecommit; no data deletion/gitclean/reset.

Next: finer causal board/private strength representation using sparse storage
(the observedAA/KK alias persists), matchednative gate, rigorousBR/error and169EV
precision; enlarge multiway action/chance support only after independentoracle
and per-seatgain gates. Approvedformalprofile decisions still needed. No formal
acceptance relaxation, registry/public/prodDB/Storage/main/Vercel/SSO/billing or
manualSUCCESS-CI operation. Ordinarycommit/push/newCI confirmation required.


## CORRECTED SCHEDULE — authoritative latest results

Review found shared-board alternating updates do not satisfy the fixed-profile
expectation test for owner1: its opponent's updated strategy depends on the same
current draw. No claim the previous entire sampling schedule is unbiased.
Original driver/native source saved byte-for-byte as transfer-alternating-source.py
and native-alternating-source.py; old outputs/commit remain intact. The previous
native performance/coverage measurements are still real profile measurements,
not evidence for an unbiased learning schedule or approved solver method.

Minimal sampled_update.py now fixes ONE pre-update pi and computes both owner
regret/average contributions against it. R0 may be written before owner1 evaluation,
but the backend reads only immutable pi, not changedR. New regression checks BOTH
owners vs independent path oracle; this combined with weighted-block expectation
proves the intended fixed-profile conditional expectation for finitechance law.
N-player hidden-world toy also verifies legal common infoset BR0 vs clairvoyant1.
Native N-owner joint algorithm is already simultaneous and unchanged.

Reproduce current corrected trial ONLY with:
`python -B -m gto.qualification.fullstreet_transfer --simultaneous --out NEW_DIRECTORY --pool docs/qa/fullstreet-generalization-20261121`
The no-flag historical alternating mode is RETIRED; do not adopt or scale it.
Selection seed+800000/final+900000 and native17122301 are NEW; earlier selection/
final/native sets are not used to select or certify the corrected policies.
Same32trainpool, source/core/tree and original16 R/S, same90sec/512MiB budget.

|seed|selection initial / first16 / final|best extra steps|final oldjoint|final old16|final corrected|
|---|---|---|---|---|---|---|
|1|8.637065 /8.639554 /8.639554|0, stop firstnonimprovement|21.612878|12.958477|12.958477|
|2|15.551498 /12.930745 /5.672675|128|23.137729|15.466930|5.281069|

Seed1 exact full pi AND average arrays equal original16; not a new improved
strategy. Seed2 is1new reoptimized research policy. Both169x3contexts exported,
not fullnative actionEV precision. Corrected BOTHseed gate FAILS, so NO method
adoption/scaledlearning. Do not replace it with earlier biased-schedule gatePASS.
10.013/56.087sec including final eval, peak462,671,872bytes. No further trials.

Independent native fresh17122301,8192worlds/172032paths,40.160sec,
peak534,593,536bytes<512MiB; same40-event family99.9% empirical-Bernstein.
SB EV seed1+.296387[-.572007,1.164781] (EXACT original16 samepolicy);
seed2+.170654[-.889758,1.231066]. Seed2 paired vsold16+.394470
[-1.077729,1.866670], not significant. Seed1 behavior identically unchanged,
CRN difference0; a conservative generic MC interval is not needed to establish
identical-policy expectation. Allnative values and intervals recorded unchanged.

Latest samecohort query rates (fractions authoritative):
seed1 turn692/2421,river763/1577,any667/8192 SAME old/new (28.58%,48.38%,8.1421%).
seed2 turn425/1788 ->17/3724 (23.77%->.4565%);
river541/1163 ->69/2048 (46.52%->3.3691%);
any428/8192 ->51/8192 (5.2246%->.6226%).
Paired seed2 worlddiff familyCI turn[-.051325,-.018499],river[-.054270,-.018728],
any[-.064808,-.027233], significant reductions; seed1 no change, so two-seed
coverage improvement gate NOT met. Prior published2048 rates stay historical.
Corrected CF visited seed1 turn58,860/river191,516 unchanged; seed2 turn87,210/
river380,492, revisit99.8968%/99.7955%. Historical array/model support, not all
physical-board information quality. Native selfplay paths differ by policy.

Corrected legal deviation gains BB (seed1 retained/seed2new), ALL intervals0inside:
3.5open +2.253601[-.183388,4.690590] /+2.379333[-.038644,4.797311]
10.5threebet +.542175[-1.276478,2.360829] /-.027649[-1.377774,1.322477]
riverjam +.107178[-1.060776,1.275131] /-.635132[-1.727761,.457498]
nuts0[-.643214,.643214] /+.005371[-.663365,.674107].
Other3probes also measured. No robustness/knownweakness-solved/fullBR certificate.
Root EV widths1.736788/2.120824BB; full169/action precision and allfullnative
BR/NC/model/omittedsize error upper bounds UNKNOWN. Formal0/12,RFI0/3bet0.

123 regressionPASS21.288sec: old121 + fixed-profile BOTHowner update oracle and
3player hidden-world BR information constraint. test_generalize now9focusedtests.
Corrected actual CP/RNG nextdraw+one simultaneousstep replay bothseeds bit-identical,
corrected/resume.json. For rejected seed1 best16 vs last32, replay ONLY
best_iterations-16=0 draws, never lastdrawsequence32. Seed2 best==last144.
Always call sampled_update.step after restoring; old Game.step is deterministic
alternating teacher, not corrected sampled schedule. No automaticresume.

Storage budget deviation: corrected extra trial temporarily reached213MiB>200.
Stopped expansion; SHA256-identical best/last NPZ content is now losslessly shared
using relative symlinks for3duplicate copies, before/after hashes verified.
checkpoint-dedup.json: no byte content lost, best originals and oldGit preserved.
Paths remain readable through links; all original509e214 CP files untouched.
Current QA~167MiB<200. Do not dereference copies blindly when packaging budgeted
checkpoints. No old research deletion/reset/clean/forcepush. New CI required for
this correction; successful CI is not manuallyrerun.

Next: do not scale either schedule on partial seed success. First improve causal
private/board aliasing with sparse representation and multi-runout chance support,
then small2seed gate on NEW final data; nativeBR/169EV/error proof before registry.
Multiway finite2deck diagnostics remain minimal algorithm work, no full6/9claim.

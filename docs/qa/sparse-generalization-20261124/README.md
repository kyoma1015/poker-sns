# Sparse generalization / adaptive sizes / multiplayer — 2026-11-24

Base d6d086de6aaa7148d09e895de4a063a413ff58da, PR120 Open/Draft. Initial8CI
families9runs SUCCESS read-only. No successful CI manually rerun. Firstrelease
scope remains all12 conditions/2..9/multistacks/positions/169EV/ante-rake/unequal
stacks. HU50 is a research milestone, NOT initialrelease. Formal0/12, verified
RFI0/3bet0; normalregistry0, existing8BLOCKED_UNVERIFIED preserved.

## Implemented and selection outcome
One existing sparse engine: compact own/public signals, exact public actionhistory,
original nativeState/settlement/chance, corrected same-preupdate paired CFR+.
Primary/secondary made rank, contributing low-hole rank, privatehigh/broadway,
pocket/suited, draw/nutflushblocker/boardtexture and prior madecategories retained.
This is still an imperfect-recall abstraction; informationloss bounds UNKNOWN.
Global suit permutations preserve features; strategically important private rank
and draw/category cases have regressions. No opponent hidden hand/future input.

Latest actual64 checkpoints imported: exactpreflop R/A by verified archive/hash/
publicprefix; new-game visits/t/RNG reset, finitewarmstart NOT inherited training
prefix. Originalpost R/A remains preserved in oldGit; post behavior uses original
corrected parent as prior where exactpublichistory matches. No fold fill.

Generic adaptive support accepts arbitrary native legal actions at any actualpublic
node. Prior independent99-root deviation discovery is now selectiondata only:
algorithm chooses top2 omitted root actions,18/19 (8/8.5BB) for bothseeds, not
hardcoded sizes. Actual root support10->12/99; omitted raises89->87. New branches
and their downstream native responses participate in jointlearning. BB10.5BB
response arises from pot geometry. Other actions/sizes remain unqualified.

Detailed vs compact sameengine,seed,budget; stages64/128 after early256rowcap
failures, no capincrease. Finalboth64 selected, no expandedtraining. Pilotv1's
point-only selection wrongly keptuntrainedt0: not eligible evidence. V2's private
rank forgetting was rejected by independent finite native322node/8worldoracle:
full-lawful finite NC .875289BB at256 vs corrected .109017BB. Independent path
CF/average/BR error <=1.11e-15. This is a6chip finiteworldgame, NOT HU50 upper.
V3 retaining all169+prefix detail still failed riverreuse gate. Finalcorrected
compact retains important made/private/draw/blocker distinctions, with remaining
lowkicker/history abstraction explicitly unverified. All trial sources/R/S kept.

## Independent final — frozen candidates, no PASS
Selection seed+2000000; final17129501 (8192), confirmation17129701 (32768).
Separate action/future RNG; native allin exact990flop/44turn or16preflop conditional
samples. Same worlds/CRN across legacyd6, detailed and compact policies. HUfamily
confidence99.9% allocation: native.0002/confirmation.0002/allrootEV.0003/jamEV.0003.
Nfinal below is its own separate confidencefamily, not combined task-wide99.9%.

| HU50 fixed-policy evidence (BB) | seed17120101 | seed17120102 |
|---|---:|---:|
| Native SB EV | .023624[-.838916,.886165] | .226311[-.700513,1.153135] |
| New minus d6 EV | -.022934[-1.078794,1.032926] | .101263[-.899923,1.102450] |
| Fresh32768 new3.5 gain | .361401[-.015964,.738766] | .307792[-.106758,.722341] |
| Fresh32768 d6 gain | .357691[-.018170,.733552] | .332202[-.084095,.748500] |
| Paired gain reduction d6-new | -.003710[-.449385,.441965] | .024411[-.398441,.447262] |
| 8BB gain8192 | .335217[-.943022,1.613456] | .132531[-1.201660,1.466722] |
| 10.5BB gain8192 | .491652[-.681207,1.664510] | .154571[-.883252,1.192394] |
| River jam8192 | .280457[-1.110666,1.671579] | -.574158[-1.827043,.678728] |

No significant qualityimprovement. Historicd1->d6 3.5BB significant improvement
is protected, not retroactively overwritten. Newcandidate is NOT certifiedsafe.
Detailed and compact have identical per-world selfplay EV values in this sample:
extra rowreuse did not establish better behavior. Do not expand this method merely
because a query counter increased. Complete native BR/NashConv upper, uniform
abstraction/continuation/omitted-size error bounds UNKNOWN. No physical bound or
absence of a found attack used as convergence proof.

| Actual independent selfplay queries | seed1 | seed2 |
|---|---:|---:|
| Turn average-trained reuse | 12/3162=.3795% | 29/3827=.7578% |
| River average-trained reuse | 0/2430=0% | 2/2095=.0955% |
| Turn both regret+average trained | 1/3162 | 4/3827 |
| River both regret+average trained | 0/2430 | 0/2095 |

Matched d6 turn/riveraverage reuse is0bothseeds. All thesequeries have >1 legal
action; no forced-one-action inflation. Coverage is on eachpolicy's own sameworld
selfplay paths, not a uniform fixed-history guarantee. Main bothseedriverreuse
objective NOT solved. reuse-decomposition.json distinguishes average-only and
actual regretupdates. No complete-quality gate passed, no learning expansion.

## All169/action EV efficiency
C++ batched frozenpolicy evaluation stratifies own169class, draws exact compatible
physical opponentcards, shares worlds/action RNG across99 actions and caches
conditional allin equity by publicstreet. No rare-hand inverseimportance weights.
64worlds/class, all16731cells/seed=33462 measured; previous676, missing32786->0
FOR RFI ROOT ONLY. Vs-open/vs3bet actionEV still UNKNOWN. Suit-orbit argument is
supported by feature invariance; no arbitrary opponent hand forced into decisions.

Whole matrix is class-CONDITIONAL forced-action EV under the SAME frozen policy.
Also save correctly weighted rootcontribution intervals: classmass*rootfrequency,
not confused with conditional EV. Max conditional interval width100BB (very wide);
max weighted-root contribution width.884494/.798996BB. Exact fold sampling cells338;
jam separately integrates all1225opponentpairs and mixedfold/call, max widths
.634978/.638006BB. Statistical measurement is NOT formalprecision qualification:
formalprecisioncells0, unverified GTO/model error UNKNOWN. Batching18.706/23.656sec,
jam2.482/2.766sec. No claim that individual rootweights prove overall EV accuracy.

## Multiplayer: sparse sampling and exact sparse averaging
Original exact3player32step restrictedgain .023738946 and old6/9 failure proofs
protected. SparseN samples full52withoutreplacement, enumerates owner actions and
fullsupport opponentproposals. N-player counterfactual reach and averageestimators
match independent fullpathoracle, including zero-target OTHER nonowner cases.
Preflop global suit orbit canonicalization preserves native cardremoval. Forced
one-action continuations are not allocated as strategyrows. Scope: fold/call/
3BBopen/10BB3bet/legalshort/fullshove, native allstreet check/call continuation;
NOT jointlyoptimized fullpostflop or allsizes.

Nodeproposal sampledaverage had maxaverageweight~38,263,752 in9max. Globaltrajectory
mixture did not remove it, rejected for expansion. Lazyaverage opt-in computes
chance(ownclass)*ownrealization*t*pi analytically for discovered infosets. Parent
links+behaviorchangepoints reconstruct ALL iterations before discovery, rather
than resetting or ignoring earlier averages. No importance clipping. Independent
3player fullpathoracle matches through8steps (atol2e-11), R and RNG bitidentical
with sampledaverage control, JSONresume exact. Averaging samplingvariance is zero
CONDITIONAL on regretpolicy history; CF learning and acrossseed variance remain.
Small .0090498 maxupdatecoefficient includes chance scaling and must NOT be sold
as a directly comparable normalized weight reduction or Nash convergence proof.

Finalsame3sec/seed pilot, completebatch boundary actual3.03..3.20sec (max+.20sec
softbudget overrun); checkpoint IO separate.6max32/35 iterations3914/4132 strategic
infosets;9max21/21,5837/5612. No fulltree/nodecap increase. Freshnative17125200+N,
256worlds, allseats, matched archivedsampled baselines; no significant EVchange,
intervals too wide for qualification. Finite3 restricted BR gains2.172906/2.930922
at64 vs sampled2.256351/3.004410; still much worse than protected exact .023739.
No unconditional multiplayer convergence claim. No expandedtraining.

Latest offline candidates:6max2+9max2, all unqualified; 7/10contexts perseed x169
frequency rows,5746 rows including explicitly untrained uniform-scope priors.
Default sampledAPI retained; lazy is explicit average_mode='lazy' research option.
Latest checkpoints/frequencies/evaluation/actual next-step proof: multiplayer-lazy/.
Old sampled checkpoint source-node-proposal.py in multiplayer-generated/ is exact
archived source for manual restore. Prior phase multiplayer-compact native eval
withdrawn because provider originally queried physical instead of canonical keys;
corrected provider regression and later generated/lazy eval replace it. First
NumPy scalar serialization failure is preserved, no lost R/A; recovery receipt
records source-class equality before controller fix. Do not cite failed/preliminary
outputs as final or formal PASS.

## Resources, evidence and restart
FinalHU puretraining+selection+save: detailed5.513/4.110sec, compact5.412/3.645sec;
puretraining compact1.661/1.332sec through128 stage, selected64. Finalpilot maxRSS398MB (allpilot peak438968320bytes),
final native~218MB. Nlazy wholepilot/eval36.451sec, peak176185344bytes, perseed
learning~3.03..3.20sec, checkpointIO1.11..3.17sec. Filesystem had6.3GiBfree.
Newtask checkpointgzip re-encoded to zstd only after exact rawSHA comparison;
checkpoint-recompression.json records original archive hashes and rawhashes.
Old committed research data never removed. QA100MiB cap; no hourslong runs.

Build native via existing build module, then sparse_solver.build(newdir,nativebuild).
Model identities include source+binary hashes; different build requires new digest
and revalidation. Manual HUrestore: load(nativebuild), module=sparse_solver.load(lib),
w,origin=warm(module,seed); q=Solver(module,w,origin,seed+1500000,sharing=True,
extra_support=pilot['extra_support'],rows=250000); bootstrap_preflop(q,old_d6_best,
rules); sparse_study.archive_restore(q,hu-final/seed/compact/best). zstd CLI required
for .zst, raw SHA checked by restore. Actual R/S/RNG next update reproduced bothseeds
(resume.json); full selected checkpoint reproduction recorded separately.

Nlazyrestore: SparseJoint(native,NativeGame([100-20*(p%3) for p in range(N)],bba=2,
rake_num=1,rake_den=20),seed=seed,average_mode='lazy'); restore(decodedcheckpoint).
Keep lazy_info/behavior_history/RNG. Actual6/9next-step proofs in actual-resume.json.
No automatic restart service claimed. Old non-Git researchDB/ZIP not recovered.

Only qualification solver/tests/docs/progress changed. No app/UI/normalregistry,
production/SQL/DB/Storage/main/deploy/SSO/billing/forcepush/destructive operations.
Local npm build/lint/browser not applicable/run. Tests and newautomatic CI are
separate from strategyquality. acceptance.json lists every formal gap/next action;
APPROVALS.md lists pending explicit profiles. No formal condition relaxed.
Next: improve jointly regret+average-trained postflop decision transfer (not just
average-only key hits), conditional size-response coverage and fullnative BR/error
certification. Lazy Naveraging is correct but does not solve low CF revisit or
postflop/model/sizing gaps. Need qualified fullscope data before registry/search.

Final evaluation executable module snapshot is final-evaluation-driver.py; later
controller-only fresh-output protection is in current sparse_study.py. Policy
kernel/wrapper/build identities unchanged. Entire selected64 R/A/prior/RNG binaries
were reproduced from original warmstart and RNG with exact rawSHA (reproduction.json),
so source append chronology is not used as a substitute for actual reproducibility.
Lazy A_visit counters describe analytic positive-average evaluations, not sampled
CF revisits or evidence that regrets changed. R counters and independent quality
remain separate. Fresh pilot output is mandatory; manual checkpointresume is
explicit and never overwrites previous research by re-running a completed pilot.

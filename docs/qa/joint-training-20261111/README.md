# Actual full-epoch vector integration, research only

All1755 orbits/22100 physicalflops/9 continuation branches, actualCFR+epoch3
regret and ownreach-average mass preserved. Legacy and vector each performed
3510board updates,one complete additional alternatingepoch4. Original parent and
engines unchanged; compressed copy-on-write overlays stayed under registered
disk guards. Explicit finite CLI and per-overlay lock, no automatic restart.

Measured training loop (Python/cache/SQLite/compression/native updates included):
legacy1350.745334CPU seconds,1364.993498wall seconds;
vector628.279293CPU seconds,634.265770wall seconds.
CPU speedup2.149912x,wall2.152084x. After-initialization call plus finalnumeric
hashing:1357.853854/635.635872CPU=2.136213x. Compilation and initial source/parent
validation are excluded. Independent BR and full parity verification are separate,
not included in training speedup. Fixed legacy-then-vector order on this runtime,
not a repeated benchmark or a general hardware throughput guarantee.
Process peakRSS633604KiB=618.754MiB,cumulative across bothbackends; no separately
isolated vector-memory reduction claim. Same2CPU/8GiB environment,one worker.

Full1755 comparison: maximumregret/average-mass difference1.1449174941446927e-15;
maximumcurrent/average-policy difference6.257001583520605e-10. Both below1e-8
preregistered threshold. Cross-backend logical/checkpoint hashes differ as recorded,
not misrepresented as bit-identical. Same-backend atomicrestart is byte-exact in
independent tests. Initial logicalhash equals actualparenthash for bothbackends.
Runtime/compiler and actualnative binary hashes are in runtime.json.

Independent ORIGINAL world-BR evaluation of bothnew checkpoints COMPLETE1755/1755.
LegacyNC4.5220148448303314/vectorNC4.522014844830331BB. LegacySB/BBBR gains
2.457878694300621/2.0641361505297104BB;vector2.4578786943006214/
2.0641361505297087BB. SB EV.13694469211204544/.13694469211204563BB.
IndependentBRwall795.060144/807.717229seconds,separate from learning throughput.
RestrictedNashConv was independently measured,not inferred from array parity.
Same-epoch original priorlegacy4NC4.5220148448303314 is reproduced; previous
epoch5NC2.934646009312 is a DIFFERENT training horizon,not a same-budget baseline.
Existing frozen0.932107BB is
still adoptionbaseline; ordinaryGTO0/formal0/12/UI0. Small delayed-output averaging
candidate passed bothtiny gates. Losslesscutoff/outputwindow API and independent
monolithicBR tests retain actualR/S and reject source updates duringevaluation.
Initial same-volume extension gate was SPACE-BLOCKED before anyextraepoch:free3374813184bytes,
required3744333904 to retain exactvector4snapshot,all1755cutoffmasses and2GiB
reserve. Deficit369520720bytes(352.402MiB). Overlays have only101/102freeSQLitepages,
so VACUUM cannot recover thatspace. No originaldata deleted,guard relaxed or
fictitious final7 result produced. Missing official20stacks/fullsizes/external comparison and model
omissions remain unchanged. RealNLHE approximation errorUNKNOWN.

Evidence: PROTOCOL.md,registration.json,legacy-training.json,vector-training.json,
parity.json,runtime.json,small-results.json. NewoverlayDBs local under
/workspace/joint-training-run; original5GB recoveryZIP unchanged and doesNOT
already include these newoverlays. Existing archive SHA reverified. Network
additional-network command stalled and ordinaryGitpush could not connect to the
sandbox proxy. Explicit approved escalation subsequently allowed normalFFpush
45dce36→aae7e74. Final evidence commit and its CI tracked in progress/PR receipts.
Never label old830CI as new-source verification. After completion, the experiment
driver gained a fail-closed existing-registration guard; no numeric work repeated.

## Registered delayed-output trial: completed, both fail adoption

Initial same-volume space refusal was preserved. Existing independent/tmp enabled
the pre-outcome storage addendum: exactsource4 snapshot stays onworkspace with
the mutablelearner; only reconstructable cutoffmass goes to/tmp. Both2GiB guards
retained. Allnew3epochs5/6/7 completed10530updates,then originalBR bothfull1755.
No history reset,policy retuning,olddata deletion or extra charge.

|Output|NashConv BB|SB BRgain|BB BRgain|SelfplaySB EV BB|
|---|---:|---:|---:|---:|
|Fullhistory7|3.113677782658094|2.038932150810659|1.074745631847435|-0.109300473345550|
|Delayed5–7|4.889039960464410|3.696431402981270|1.192608557483140|-0.383466170258237|

Bothworse thanimmutablefrozen.932107153,0.1BBFAIL,noadoption. Full7 is also worse
thanprior5NC2.934646009 by.179031773BB. Smallteacher128 gate did NOT transfer to
this early genuinepopulationhistory; this is a limitation,not evidence that
moreepochs/strongerdelay will fixquality. Completednegativecomparisons retained.
No causal claim that nonmonotonicity alone proves an implementation bug.

Allmain4contexts169rows/2028actionEVcells peroutput,1352rows/4056EVcells total.
Positiveactualaveragemass support full7=169/169 each; delayedRFI169,vsopen169,
vs3bet168,vs4bet68. The102remaining delayedrows are explicitly ZERO_AVERAGE_MASS_
UNIFORM_EXTENSION,not sold as learnedconditional169GTO recommendations. New
evidence exporter binds sourcecheckpoint/frequencies/mass and rejects mismatch.
Newresearch8contexts are artifactsonly; existingUI8ranges1352rows unchanged.

AVERAGING_IDENTITY.md distinguishes policyEV from minimaxvalue bounds and checks
realization-average convexity. ObserveddelayedNC4.88904 exceeds derivedlowerbound
2.3312683; no newmodel,externalreference or acceptance criterion was introduced.
Formal0/12,ordinaryregistration0,UInew0 remain unchanged. Next research priority:
extract an actual legal pureBR policy from qualifiedvalueoracle,validate its payoff
against independentBR,then a budgeted restrictedstrategy/doubleoracle comparison
on matched early-history smallgames. Avoid merely repeating moreCFRepochs or
using a teacher128 success as proof of teacher3 transfer. Richergame/calibration
and formalregistry/reference evidence are still required before ordinaryrelease.

# SparseN-player external-sampling gate — fixed before pilot outcomes
Source d6d086de6aaa7148d09e895de4a063a413ff58da. Reuse Joint, actualNativeState,
OfflineProfile and exact3player terminal-path oracle. No oldCP/result overwrite.
Action scope remains finitepreflop3BB/10BB/legalshove + realnativepostflopcheck/
call continuation. This is NOT alllegal sizes or joint fullstreet game coverage.

Correctnessgate: exact native3player [24,22,20]chips/fourAA-KK-QQ worlds, full
expected rawregret and realization-average equality to terminal-path oracle,
including targetzero for a thirdplayer. AllNowners use SAMEpreupdatepi and one
independent chance draw; Nactionstreams. Otherplayerssampleq=(1-eps)pi+epsuniform,
eps=.2, fullsupport. CFprefix prod(allotherplayers targetreach)/sampleprefix;
futurepi/q corrections. Average from nonowner traversals ownreach/qprefix, summed
and dividedbyN-1; timeweight asJoint. No q=pi-zero-support shortcut. An audit
full-q enumeration exercises the samecollector, not another learningmethod.
Atomic batch: no R/A/actions/counters commit before allNtraversals complete;
cap/overflow rolls masterRNG back and stops, never redraw-until-accepted bias.

Then exact3player finite sparse64steps/2fixedseeds, <=5sec each, measure SAMEfinite
BR/path law. Only if expected-estimator/schedule/resume gatesPASS proceed to native
6/9pilot,2seeds perN, each<=3sec PUREcompute/max64completeiterations. Checkpoint
serialization measured separately. Sparsecap20,000nodes/completebatch,2sec/batch,
8,000infosets; cap stops and saves preceding completeR/A/RNG, no partialbatch.
Native6/9researchstacks[100,80,60]repeatedchips,BBA2,5%rake (not formalspec adoption).
Chance full52permutation; all2Nholecards/board sampled without replacement.
Initialprior uniform within explicit scopedlegal menu, neverfoldfill.

Freshnative eval256worlds perprofile/seed, independent seed17124200+N; frozen
learned/initialprior same deals+tapes (profile sensitivity, NOT unilateralBR).
AllseatEV/rake and paired differences recorded;80simultaneous Hoeffdingintervals (45seatmeans+30seatdifferences),
family99.9% boundssamplingonly. Rootseat2immediatefoldutility exactly0 supplies
legaldeviation lower fromnegativeprofileEV; no fullBR/NashConv upper substitution.
Untrained-average path/decision counts are diagnostics, not equilibriumcoverage.
No post-selection seeds or longtraining. If no significantnativegain, no expansion
or ordinaryregistryadmission. Budgettotal120sec, memory256MiB target, QA20MiB.
Legacy2..9tests rerun only because sharedmodule changed; no manualCIreruns.

Before final proposal comparison: nodewise eps mixing produced measured9max
averageweight max38263752 (no clipping). Sameengine alternate trajectorymixture
q(prefix)=(1-eps)prod(target)+epsprod(uniform), conditionalposterior probabilities
computed logstable. Existing raw N-owner CF/average zero-target oracle must PASS.
No target/chance/average objective change. Same seeds/3sec budget/caps; oldnode
CPs/source/evaluation protected. No further proposals after this bounded gate.

Trajectoryproposal failed maxaverageweight gate:9max still38263752, no expansion.
NEWanalytic sparse averaging: chance(own169class)*ownreach*t*pi; exact parent
links and behavior changepoints reconstruct ALL pre-discovery iterations, no
missing-time reset/importance clipping. Preflop-only; forced continuations excluded.
Independent3player fullpathoracle verifies every discovered A through8steps,
including retrospective periods; R arrays and RNG identical to sampledaverage
control; JSON checkpointresume bitexact. Same3sec/seed/caps, fresh final17125200+N
256worlds. Compare archived nodeproposal/sample-average policies on SAME fresh
worlds, all-seat sensitivity not unilateralBR. All-seat160event CI budget.
Default sampledAPI retained; lazy is explicit researchopt-in, no admission.

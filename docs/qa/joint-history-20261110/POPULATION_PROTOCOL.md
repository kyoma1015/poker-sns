# Population deployment after small-game gate PASS, before running population

Two independent64x64LP/64pureBR games pass dualgap and legal-information tests.
Retaining actual R/S, alternating finalNC0.002065107124/0.001286569559 versus
simultaneous0.004591451622/0.002808321665 (both<=75% and improve their initial
baselines). Other history-reset/damped results retained; damping not deployed.
This selection uses the same optimization games, not holdout/external validation.

Deploy ONLY full-population alternating RM+linear average, BOTHplayers completing
all1755orbits before the next player's preflop update. All22100physicalflops,
original9continuation branches,HU50/noante/norake/same2.5/9/21/50 and3flop sizes.
Keep frozen baseline0.932107152722. Parent is the ACTUAL cfr_plus epoch3 R/S state
(/workspace/joint-updates-run/cfr_plus.sqlite),NOT the frozen behavioral profile.
Parent current NC4.888656674494 and all original worse results remain unchanged.
This is switching update order with genuine history,not inventing regrets for
frozen teacher. The tiny epsilon prior originally in parent is disclosed.

Fork parent into a NEW independent SQLite, verify every inherited numeric byte
before changing only metadata/clearing cached eval. Preserve actual3iteration
R/S and continue linear weights t4/t5. One epoch=fullSB population thenfullBB
population; postflop rows belong to board/ownprivate observation, preflop rows are
shared. Deferred preflop counterfactual gradients integrate fullboard chance
before update. Each owner's average uses its own reach; BB's own strategy does
not change during preceding SB update. No board-specific preflop policy.

Exactly2new outerepochs,target4/5; actual independent originalfullBR at each.
One finite invocation3600s including fork/train/evaluation. If incomplete, retain
partial cursor/phase/safe intervals, do not extend time after seeing results.
2CPU/8GiB cgroup,newcheckpoint3GiB,filesystemfree>=4GiB. Existingexactcache reuse,
no additional paid resources. No damped update or post-result model selection.

Adoption rule: compare BOTHfull snapshots to frozen0.932107152722 with1e-8guard,
retain baseline on ties/worse. Population research target remains<=0.1BB. Even
passing that cannot qualify fullNLHE/normalGTO; formal0/12 and normal0 unchanged.
No new range inUI,existingfrozen/ranges/HU1BB/2–9/demo preserved.
No best-checkpoint selection may be called a holdout result. Alltrials saved.

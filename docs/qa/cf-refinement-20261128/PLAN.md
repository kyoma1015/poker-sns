# Active CF refinement gate (before implementation)
Base5ca70afcb80e8b5348bffbe1b5d8471a90aabc55; Open Draft;9baseline runsSUCCESSattempt1.
No release criterion/specification changes. Formal0/12/RFI0/3bet0.
Scope C-only: new solver modules/tests/evidence, qualification workflow, C progress.

Primary gate: derive causal feature split priorities from one-step CF Jensen gaps
on fresh selection catalog seed17160101+seed (NOT old final17154101/catalog17153301).
Preserve previous policy for unseen refined keys, exact cumulative optimizer on
unchanged keys; new split rows R/A0, not invented historical regrets.
Compare before/after same chance/action law and native policy; reject if initial
behavior changes. Local split scores are NOT summed into a native BR bound.
Candidate/control share training fresh world stream and pureCPU budget180 perarm;
measure same selection coarse/fine BR at0/90/180,8split max/seed,10Mscalarcap,
2CPU/8GiB,one learner at a time. Extend only if fineBR improves vs control and
native paired pilot does not detect harm. Last/selectionbest remain separate.
Freeze before new final catalog17160301+seed/native17160401 (old final neverselects).
Independent fullnative upper/chance/size/continuation errors remainUNKNOWN unless
certified; no ordinary registry. Preserve all oldCP/rawJSON/frozen/HU1BB/8candidates.

Storage: implement reversible array XOR against aligned immutable old checkpoint;
validate exact reconstructed SHA256, tamper rejection, real nextstep RNG equivalence.
No olddata deletion; savings apply to newdelta bytes, not historicalrepo size.
Other gates: generic size support bounded expansion/oracle, N sampling variance
and cap diagnostics; no adoption from one improved seed. No generalN Nash claim.

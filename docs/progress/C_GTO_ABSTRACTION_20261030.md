# Preflop abstraction batch
User explicitly prioritizes a separate preflop abstraction solver over exact full
postflop resolution. Starting public7aefafa97a7440b5a0bf03ea7662e622fd853156,
locale3b75c26abc096e7e672a6b0533db3c0123b0a9e/tree4a6f47732a2b0ae8af2d0db9959eb38217d44ed9,
clean. Preserve original native modules, HU1BB, all2..9 regressions and UI gate.
Acceptance before implementation: HU50BB/SB1 BB2 chips/100 each, no ante/rake,
explicit research sizing5/18/42/100chip raise-to. All-in showdown uses actual
compatible four hole cards and board without replacement. Exact169x169 joint
class mass includes blockers, not independent class products. Compare checkdown
and public-flop/own-hole fixed betting controllers (no hidden opponent/future
policy inputs, no constant EQR). These controllers are continuation abstractions,
not full postflop equilibrium. Learn the entire finite preflop abstract tree with
CFR and compute exact information-constrained best responses within that sampled
payoff game. Independent payoff seeds, sampling intervals and model sensitivity
are separate from abstract-game NashConv. No reference solution currently supplied;
mark comparison unperformed. Generate169frequencies/actionEV/conditions for RFI,
vsopen,vs3bet,vs4bet. No real-game GTO certificate or UI admission by coverage alone.
Tests: independent chance mass oracle, hand rank oracle, chip conservation,
conditional reach, legal betting, exact small-game BR, CFR/BR improvement,
reproducibility; pinned local C++ build and dedicated CI. No new dependencies or
paid services. Only GTO code, dedicated CI, evidence/docs modified.

Local implementation: separate stdlib C++/ctypes kernel and full-tree CFR; native
rank5/rank7 extracted from hash-verified existing header. No extra dependencies.
Exact joint1624350 compatible unordered-combo seat assignments. Full public
abstract tree28nodes includes limp/check, fold/call, raises5/18/42/100, and true
all-in showdown. Non-all-in controller uses own holes/public flop only, one
half-pot bet, then turn/river check-through. Checkdown is a comparison, not the
only continuation model. These are fixed controllers, not solved postflop play.
Two independent payoff seeds1701/2901,256worlds per unordered class pair,
3677440worlds per seed; shared swapped seats and continuation planes are NOT
independent extra samples. Four4000iteration CFR runs, exact within-sampled-game
information-constrained BR, same-input solver replay. Model NashConv0.00254675,
0.00262342,0.00256855,0.00262724BB;100iteration values around0.098BB.
Independent frozen seed1701 policy tested on seed2901: checkdown SB EV
-0.04734502BB interval[-0.14849818,0.05380813]; flop controller0.02089659BB
interval[-0.05420269,0.09599588].99.5% each/99%both, weighted Hoeffding over
independent class-pair/world groups, keeping shared-plane/seat correlations.
These intervals concern fixed abstract-model policies, NOT real-game error or
NashConv. Uniform169hand/payoff bounds remain18.3113BB, too wide for release.
Seed-to-seed maximum hand-frequency differences92..99percentage points;
reach-weighted TV distances5.13..13.25%. Small sampled-game NashConv alone is
NOT convergence of the expected abstract game or accuracy against real poker.
No trusted matching preflop reference; comparison UNPERFORMED. Real-game error
UNKNOWN. Formal acceptance0/12 retained. Research UI contains2models x4contexts,
169hands each, explicit opt-in, exact conditions, no formal catalog admission.
Tests local:8C++/Python native oracles PASS,56existing pure PASS,13Node PASS.
Local npm build blocked: no installed TypeScript and npm dependency acquisition
EPERM at configured proxy. Use authorized GitHub Actions npm/build/lint/browser;
do not disable checks or alter SSO. Source tree/CI changes are GTO-only. Full
existing native regression workflow retained; new abstraction workflow builds,
tests, recomputes independent seeds and compares research output provenance,
frequencies and EVs (float tolerance1e-12, identity hashes exact). CI pending.
Release is not complete: reference comparison absent, class-level payoff intervals
wide, seed-sensitive hand frequencies, expected-controller-game convergence not
certified by convergence of a fixed sampled payoff table. Research results are
opt-in only and never fed to findVerifiedRange. A matching query requiresHU50,
correctactor,2.5/9/21sizes,noante/rake; other conditions return no research range.
Next: use independent validation to improve payoff estimator/continuation models,
compare a trusted same-condition reference, then certify approximation accuracy
before any ordinary GTO admission. Do not merely increase formal acceptance.

CI41085432081 failed research replay at a1e-12 EV comparison despite identical
payoff table hashes; whole-game metrics differ at~1e-16 and raw policy digests
differ. Investigate cross-compiler FP optimizations; do NOT increase tolerance or
ignore policy digests. Fix plan before edits: explicit-O2,-ffp-contract=off,
-fno-tree-vectorize; preserve arithmetic tests. Recompute the artifact under
these pinned flags and rerun the failed CI. Add fresh validation seed700017,
preselected before new evaluation, distinct from exploratory seed2901 and the
additional local seed500017. Archive raw kernel and full frozen public-tree
policies in experiment output for subsequent independent audits; these are
local/ephemeral CI outputs, not production Storage writes. Original engines
remain unchanged. Separate legal/debit audit using preserved Python Betting
passed27preflop edges and2000controller/all-in terminal settlements with zero
conservation or cost-basis mismatches; all1352UI fold EVs match past contributions.
FMA root cause confirmed, not just inferred: local-mavx2/-mfma reproduces failed
CI checkdown policy SHA7efb7bdc96df857347480c1ace3feacfb334725b30960f04330c5a864477724c,
NashConv0.002546750564182486 andSB EV-0.04698984138094505 exactly. Explicit
nonfused O2 build keeps the original local reference values. See
fp-replay-diagnosis.json. No tolerance/digest gate weakened.
Canonical local fresh seed700017: checkdown fixed SB EV-0.04731059865721331,
99.5%interval[-0.14846375322092353,0.053842555906496906]; flop controller
0.01981889930421947 interval[-0.05528038842974989,0.09491818703818883].
These replace the exploratory2901 heldout display; training/comparison seeds
remain1701/2901.4CFR runs,3kernel seeds; same-input replay is not additional
independent data.8native tests,13Node tests and2000ledger checks PASS locally.
CI rerun required for the FP fix; old successful checks are not manually rerun.
Full model policies and raw kernels archived under experiment output (local
/workspace/gto-abstract-canonical-fp); not permanently uploaded/production data.

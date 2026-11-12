# Findings: bounded correctness versus early optimization instability

Nine independent tests found no discrepancy in native CFgradients, own-reach
average weights, hidden/future-card information, signs or BR normalization in the
small enumeration game. All64 pure responses per player are enumerated, not just
a second implementation with the same recursive best-response algorithm.
The asymmetric2x2 exact equilibrium verifies schedule convergence independently.
This is bounded evidence, not proof of the entire production implementation.

The old so-called warm start R=1e-15*pi,S=0 transfers a behavioral policy only,
NOT its historical regrets or iteration count, NOT a Brown/Sandholm regret-transfer
warm-start certificate. Initial fixed-policy accuracy is not a monotonic floor.
On three actual frozen-board blocks, raw maximal CFgradient/epsilon ratios are
2.58e13/3.85e13/2.59e13 (before orbit weight); audit-results.json also records exact
orbit weights and the corresponding weighted ratios. The first true updates
therefore overwhelm the prior. This is not a chance/reach normalization bug.

Independent analytic near-equilibrium witness is in near-equilibrium-witness.json:
A=[[2,-1],[-1,1]], start p=.400001,q=.399999 near p=q=.4 equilibrium. Correct regret
updates from epsilon policy priors can produce a much worse2iteration average.
Numbers are artificial ANALYTIC GAME data, NOT measured HU50 EV or GTO accuracy.
They demonstrate a mechanism consistent with the HU50 early degradation, not a
proof that this is its sole cause. Small hidden-card curves also exhibit genuine
nonmonotonic NC steps with independently enumerated BR (audit-results.json).

Important identifiability result: first2current behavioral profiles are identical
for vanilla/CFR+/DCFR with these initial conditions; CFR+ clipping is RM-equivalent
at first update and DCFR t1 scales both signs by.5. Thus the full-population
linear-vanilla/CFR+ epoch2 equality is EXPECTED. Their regret-schedule differences
first appear at epoch3; DCFR epoch2 average differs because weighting is1:4,
versus1:2 linear and1:1 uniform, not because its second current policy differs.

Training-only native kernel omits unusedBR and preserves gradients/averages bit
for bit. Three measured CPU cost ratios are.685510/.707979/.732252 of fullkernel.
This is a small cost sample, not a promised whole-population speedup.
No old solver source, frozen policy, UI or model parameters were corrected here.
Reporting guard separately treats<1e-8 floating-point changes as no improvement;
4e-16 differences must not become a claimed quality improvement.

Full-population2epoch results further isolate the early second iterate: uniform
average1.190819543932,linear1.475248875070,quadratic1.775081253887BB, against frozen
first profile0.932107152722BB. Those averages mix realization plans with1:1,1:2,
1:4weights. NashConv is convex in the two realization plans (sum of maxima of
linear BR values). Thus the COMMON second current policy has NC at least
(5*1.775081253887-.932107152722)/4 =1.985824779178BB. This is a DERIVED LOWER BOUND,
not a direct BR measurement of that policy or a real-game precision statement.
It certifies early-update degradation in the finite game, consistent with tiny
behavioral initialization/no inherited regret and simultaneous-update transients.
It does not establish that arbitrarily increasing iterations will solve quality.

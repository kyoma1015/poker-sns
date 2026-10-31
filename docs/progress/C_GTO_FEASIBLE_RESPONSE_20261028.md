# Feasible full-continuation response assessment — 2026-10-28

Input public9bec2897281ad43dd18c7e79f4b3a63844e08cc9/local e197932,
same tree4f115fb7e1da09fd6acc18f8a52682dfca47ad55,CI40612169704 and
40612169502 SUCCESS685PASS. Initially clean. Work onlyGTO/native/tests/workflow;
no shared application edits, original solver/checkpoint/evidence bytes preserved.

Acceptance before implementation: retain full52card HU50BB game, all bet sizes
and real future player decisions; implement information-set-feasible response
learning against a frozen opponent, and independent held-out terminal evaluation.
A positive feasible gain is a LOWER bound against the named fixed total profile,
not an upper bound/exact best response/equilibrium certificate. Do not release
ordinary GTO data from local EV, policy drift or a single candidate's failure.

Analysis: ordinary_study uses2worlds/class,64nodes/traversal; known utility span
and concentration saturate at100BB. world_bounds reveals opponent/future cards
to the maximizer; even infinite search can remain intrinsically above a true
information-set best response. Missing-policy intervals widen it further.
Simply increasing nodes/samples cannot repair the information relaxation.

Plan: preserve strict PolicySnapshot/missing semantics. Add an explicit,
research-only total-profile declaration: frozen owner-updated averages plus
uniform-legal prior completion ONLY when explicitly enabled. This corresponds
to native unvisited average initialization, but IS NOT a learned/verified row.
Report completion usage separately and do not treat this completed profile's EV
as certified EV for the original partial learned strategy. UI gate unchanged.

Use preserved solver's generic single-updater path: opponent decisions become
chance with immutable information-set policy probabilities, native card chance
and betting states remain actual NativeState. Hero learns full-continuation
response at own native information keys. Hidden opponent cards/future deck are
never available to policy decision logic. Train/evaluate seeds disjoint. Freeze
response, save source/config/opponent-bound fresh checkpoints and policy digest.
Evaluate full terminal trajectories with chip/rake conservation, per-class and
whole-profile intervals, candidate gain CI and empirical completion usage. A
zero/negative lower bound is inconclusive, not proof of equilibrium.

Improve rare-prefix support by extending targeted100000iterations while keeping
50000observations comparable. Preserve genuine posterior weighting and nullEV
for unverified ordinary ranges. Formal12acceptance0until actual evidence passes.
Existing pinned CI is native runtime path; no repeated network permission request.
No production/main/billing/scheduler changes or independent restart activation.

Response training keys merge only the two private-card DEAL ORDERS, at every
street. Suit labels/ranks/board/history/all legal actions remain exact. This is
an exact redundancy removal against the fixed opponent: it cannot observe the
hero's private deal order; physical chance/payoffs depend on the same two-card
set. Do NOT merge suits against a possibly suit-asymmetric fixed policy. The
response declaration records unordered-own-card keys; base policy keeps its
original native keys. Predetermined response checkpoints1000/10000; held-out
samples12000 at seed100017, training seed701. Selection never uses held-out gain.
Uniform completion remains explicit and its decision usage is reported. All
computed moments refer ONLY to the completed profile; original partialEVnull.

First full run4e1073c53eca0de8ff2bdf89eb6d4933c03ff84b:
native40617708986 SUCCESS662unittest+25Packed; UI40617708924SUCCESS17,
combined704PASS.12000held-out worlds: completed-base SBmean-3.3366667BB,
simultaneous CI[-5.3119293,-1.3614040]. Learned10000iteration candidate mean
-3.7165417BB,paired gain-0.379875BB,CI[-2.7690763,2.0093263]: no improvement
proved. Base34335completed/15264observed decisions; candidate35172/13783.
This is NOT original partial learnedEV; no ordinary GTO/UI acceptance.
100000targeted:seed17vsopen/vs3bet/vs4bet169/169each;seed29vsopen/vs3bet169,
vs4bet165(updated2648/2652). True prefix weighting retained.

Exact SB always-fold is a FULL deployable root strategy, value-0.5BB by actual
NativeState terminal settlement, independent of hidden cards. Compared to the
FULL ex-ante completed-base EV, gain CI is[0.8614040,4.8119293]BB on the same
simultaneous confidence event. This is a valid whole-game deviation LOWER bound
for the completed profile, not a local handEV used to claim Nash accuracy. It
rejects that completed profile's convergence; says nothing definitive about
unspecified completions of the original partial model. BB has no such exact
initial-fold control, so it is withheld when hero is not the initial actor.
Add actual native control test; keep trained candidate's inconclusive interval.

Also restore actual10000response checkpoint into a fresh solver, check policy
and RNG, replay the exact same12000held-out worlds and require identical raw
moments/trajectory hash. Replayed samples are NOT an independent replicate and
do not double statistical sample size. First-run JSON preserved outside repo at
/workspace/gto-feasible-response-first-4e1073.json for cross-run comparison.

# Joint reach integration protocol (before execution)

Base: f7b9e54ffbdc1dde4a8fecec6018dc8d78e45b52. Research only. No normal
GTO admission, no changes to frozen policies, existing datasets or demo.

Implement one joint extensive game: existing HU50 preflop tree, all nine matched
branches, three flop sizes 1/3,1/2,3/4 pot, one raise, exact conditional showdown
over all 990 runouts. Future betting remains omitted. Own information is starting
169 class, public flop, own/public flags, and full public action history. No
opponent actual private signal or future runout enters policy lookup.

First integration experiment uses the first THREE representatives in the already
used suit-exact design. This is a known-board integration study, NOT an unseen
generalization experiment. Probability is the exact physical chance CONDITIONAL
on this registered board subset, weighted by orbit multiplicity. It is NOT full
board coverage or a full-game root EV. The interface must allow additional orbits.
Do not compare its values directly against previous full-population BR numbers.

Compare uniform joint profile and synchronous full-sweep CFR checkpoints 16,64,256
in the SAME finite game. Report every checkpoint, including deterioration. No
seed/model selection: complete conditional enumeration, no Monte Carlo seed.
Also evaluate the frozen learned_small preflop/coarse continuation profile on
exactly this same board subset/action game, with read-only information refinement.
This is an integration comparison, not a comparison to its published full-board
numbers. No existing policy is modified or replaced.
The chance tensor is unweighted by either preflop policy; card removal enters
joint hole-pair mass before learning. Average strategy uses own reach; regret
uses chance times OPPONENT reach only. All histories, including own-zero-reach
branches, must be traversed. Independent BR shares preflop information across
all future boards and maximizes only AFTER summing their conditional values.

Predeclared tests: own-zero-reach counterfactual updates, opponent-only posterior,
no future-board preflop observation, no opponent-private policy key, regret
bound versus independent BR, chance normalization and conservation, exact small
game native/Python parity, legal cashflow, immutable old artifacts. Numerical
tolerance 1e-8 BB, probability tolerance 1e-10. Research convergence target 0.1BB,
not a full-poker precision guarantee. Unmet criteria are recorded, not waived.

Future nonallin showdown mass is assigned a conservative [-50,50]BB root payoff
envelope. This is a missing-game bound, not statistical uncertainty. External
GTO comparison remains unperformed and real-game approximation error UNKNOWN.
Formal acceptance remains 0/12 unless independent qualifying evidence exists.

# Exact streamed joint learning protocol

Base c1855e86128eeaf5a7446c699dce91d4dd4836ea. Preserve every old pinned source,
dataset, static demo and UI. Research only: formal0/12 and normal registrations0
unless independent qualification actually changes them.

Use all1755 registered suit orbits, multiplicities summing22100, and the unchanged
HU50/noante/norake/2.5,9,21,50BB preflop tree + three flop sizes, one raise,
checkthrough future streets. Private169+own/publicflags and exact public board
history, no opponent hidden cards in action lookup. Unweighted card-removed joint
moments are exact over compatible holes and990runouts. Existing3board cache may
be reused only when its moments match a fresh independent calculation; cache
identity pins the producer dependencies, not just a board filename.

Each exact epoch freezes the SHARED preflop regrets/strategy across every board.
Accumulate chance-weighted counterfactual gradients and own-reach average weights;
commit the shared update only after a complete population sweep. Board-specific
postflop rows can update after their sole block because they are disjoint.
SQLite transactions couple each board-state write with cursor/preflop-accumulator
updates. Crash/restart must reproduce uninterrupted state; checkpoint identity
includes source/game/chance and epoch. No per-board preflop reoptimization.

Independent BR aggregates conditional terminal counterfactual values by own
starting class across ALL boards BEFORE preflop maximization. Optimizing root
separately by future board is prohibited. Evaluate uniform/frozen baseline and
completed epochs1,2,4 where resource budget permits; report every completed
checkpoint, including worsening. Target joint restricted NashConv<=0.1BB; never
infer external GTO precision from it. No new unseen-board/generalization claim.

Limits: one board in RAM, conservative working-set guard2GiB, disk cap12GiB,
per-invocation wall budget and bounded board/epoch counts with resumable exit.
First measure full cache/epoch/evaluation costs; further epochs only within these
limits. Never substitute missing blocks with0. Partial evaluations keep safe
[-50,50]BB profile / [0,100]BB NashConv bounds and explicit chance coverage.

Validate: chunk vs monolithic CFR and independent BR, preflop future-information
counterexample, opponent-only counterfactual reach, all9cashflows, normalized
169rows, exact chance mass, interrupted vs uninterrupted replay, wrong identity
rejection, budget stop without lost work, old artifact hashes. Tolerance1e-8BB.
Existing 28/22100 study remains a different conditional population. Old full-board
BR3.244178/2.608232 and TT model gap7.647099 are not automatically resolved.

Added sizes, second raises, future betting and private abstraction remain separate
model omissions; maintain conservative bounds. Formal20stack/fullsizes and legal
matched external references remain evidence gaps, not permission to shrink scope.

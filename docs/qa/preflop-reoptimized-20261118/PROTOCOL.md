# HU50 coupled-payoff preflop policy iteration (research only)

Before implementation: preserve all previous artifacts. No registry admission; formal 0/12.
Scope: isolated HU50, zero ante/rake, existing 3/10/50 BB reduced tree; no formal specification adoption.

Public-board importance sampling, exact disjoint private-card enumeration, full three-street rollout of the existing range policy. Policy sees current board only. Public action coins shared across hypothetical hands; independent units are boards, NOT private pairs. Multiply board samples by C(52,5)/C(48,5), divide class sums by exact preflop compatible counts. Fold leaves exact. No unknown-history fold fill.

Pilot: one board, 60 seconds; production gate at most 8 boards/300 seconds/100 MiB; checkpoint each completed board. Abort an incomplete board, never treat it as zero. CFR 100 iterations for matched passive-control and active kernels; same chance, samples and compiler. Save every frequency/model EV and both digests. Runtime current-chart ranges may differ from old-chart anchored training kernel: coupling error UNKNOWN.

Independent native evaluation: fixed fresh 256 root worlds, 90 seconds; identical worlds/tapes old B/prior range/new range/matched control. Test 3.5 open, 10.5 3bet, river jam and general river nuts. Family 99.9% intervals. Expand learning only if paired native improvement lower bound >0 and no positive deviation lower bound; otherwise stop. Complete BR/NashConv/omitted-action error and full native 169/action precision remain UNKNOWN until measured. No physical payoff cap used as convergence evidence.

Regression: exact chance weighting, no hidden/future policy input, pair aggregation vs scalar, deterministic public sampling, changed 169 rows, checkpoint resume identity. No app/UI/shared production files affected.

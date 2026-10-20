# C active development acceptance (before implementation)
Base: PR13 / 3ca87764e988cac588fef915d48823702a1a3326.
Milestone 1: pinned reconstructed (not original G11) dependencies; separate untouched-source Next/Cache/Packed builds, separate-process imports and numeric-boundary smoke tests; all failures retained.
Milestone 2: reusable native probability/regression and temporary-checkpoint harness on synthetic data; reject incompatible contracts/invalid probability, benchmark reproducibly. No historical G11 equivalence claim.
If reconstruction is impossible: implement independent 169-hand mapping/aggregation and checkpoint validation with tests; do not mark native work complete.
Shared files affected: only C progress, gto/, GTO test/workflow additions. No A/B/D source or production DB.
Full final scope retained: 2–9 players, 20 stack configurations, ring rake, BB ante, MTT chipEV, specified bet sizes, 169-hand frequency/EV. This batch is a prerequisite milestone, not a reduced final solver.

# Fixed native qualification attempt, registered before measurement

Reuse completed candidate/certificate/search pipeline unchanged. Conditions are
EVALUATION_ONLY until proposalA/B/C approval: HU50 MTTchipEV,ante/rake0,BB2chip,
SB RFI and BB facing SB raise-to5chips. Full52-card deck, all streets, all native
legal integer-chip bet sizes, not the restricted270-node game.

Two existing source models, learned_small/large. Define explicit TOTAL evaluation
policies: same preflop rows/coarse flop tables on known histories; round model
flop wagers upward to legal integer chips, cap to stack, merge aliases by public
canonical child. Unsupported histories: fold facing a bet, otherwise check.
Turn/river check/fold completion. This is an evaluation-only policy completion,
NOT proof that original model already defined full-native behavior. New policy
identity includes completion/rounding, source and native rules.

Reference betting uses preserved Python ledger with an explicit short-all-in
sentinel for target1chip (raw1 otherwise collides with call). No original source
modified. Compare all action sets/actors/transitions/terminal settlements against
thin native C++ State on first256baseline paths per context/model; also compare
pure Python vs C++ hand ranks there. No private/future observations in policy.

Fixed samples16384accepted deals per context/model, seeds20261117(+1009model,
+17context). Vsopen deals are rejection-sampled by the SOURCE SB open probability,
not uniform opponent ranges or solver visit counts. All169class EVs reported;
zero/insufficient samples remain unknown. Per-hand intervals are NOT expected to
meet0.05BB at this budget. Confidence union bound across4reports*(2*169+4)metrics.
Paired empirical Bernstein with bounded payoff support; not a numerical roundoff
proof. Non-exact empirical assertions cannot manufacture a full BR upper bound.

Feasible deviations: SB open-to3BB at RFI, BB3bet-to10BB facing open2.5. Both are
legal omitted sizes and use no opponent/future cards. Report gain LOWER bounds,
never an independent full BR upper bound/NashConv. Vsopen conditional gain is
also multiplied by exact source open-history reach for a root feasible gain.
Compare native realized baseline to model terminal cashflow on coupled paths:
execution/rounding discrepancy only, not uniform continuation error over all
possible deviations. Full-model error upper bound remains UNKNOWN unless proved.

Hard evaluation stop180s, disk reserve2GiB, saved cursor/RNG/moments every1024
deals. A paired gain lower>.05 refutes the proposed threshold for this completed
policy. Missing full BR upper/uniform-model-error proof/169 EV precision always
blocks registration, regardless of absence of a found counterexample.
No learning, no full population retraining, no automatic resume, no ordinary data.

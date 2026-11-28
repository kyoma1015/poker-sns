# Corrected-average HU50 action baseline / reach proposal gate

Start78368cb; frozen corrected checkpoint c848... and all old audits reused.
No formal specifications adopted. HU50/native0.5BB chips/zero ante/rake only.
Four arms: zero/control, action-baseline, reach-proposal, both. All warm-import
corrected R/S/RNG, no reset. Same seed stream, target2sec/max512pairs each,
checkpoint32pairs; storage20MiB, total local compute5min. Atomic step may slightly
exceed time cap. No recursive external expansion after its prior negative gate.

Baseline predictions are fixed BEFORE paths from prior all169/action EV artifact
(root and vs3BB only), plus known fold payoff elsewhere. No opponent/future cards.
They are control variates, not substitutes for true terminal utility. q>=positive
uniform mass retains ALL legal actions. Reach proposal mixes uniform with3BB open
or10BB3bet at those exact public prefixes, both players; target pi is unchanged.
Use GENERAL pi/q prefix and suffix corrections, including opponent zero targets.
Average remains non-traverser own-realization/q-prefix; pair R frozen.
Independent finite oracle must match CF AND average expectations for arbitrary
baselines, proposal!=pi and zero target before training.

Frozen diagnostic3seeds x256paths per arm, no updates; record CF dispersion and
3BB/10BB positive average reach. Independent native paired evaluation32768worlds
per policy, same deals/action random tapes, <=90sec total, no training.
Profiles are4averages plus current-regret control and combined, declared before
any native outcomes. Current policy selection is not averaged-policy convergence;
compare current combined with current control separately. Three
average candidate/control differences, current-regret control/combined difference,
current/average control contrast and6profile means form11 simultaneous empirical
Bernstein intervals, family99.9%. Point improvements alone do NOT pass.
Stage gate: candidate paired EV-improvement LOWER>.1BB and lower fold-gain upper
than control by>.1BB. Select among simultaneous intervals; then at most ONE extra
matched2sec/512pair control+candidate stage, fresh native holdout seed. If no gate,
stop immediately. No all-population training. Resolving fold weakness requires
native fold-gain UPPER<=0, separately reported. No ordinary registry admission
without complete BR upper, all169/action precision and approved formal conditions.

Reuse existing CRN all169/action evaluation for final control/candidate; add
conditional integration at all-in fold/call nodes, exact fold EV intervals. Compare
with unchanged estimator on same worlds/tapes; independent finite/native oracle.
Never compare root-only precision with all169/action precision as solver progress.
Full BR/NashConv point/upper remain unknown when uncomputed, no physical substitute.

Execution note: pilots with seed17112026 overlapped the fixed baseline prediction
artifact; preserve them as pilots, exclude from independent admission evidence.
Final all169/action validation uses fresh seed17118091. The metadata field formerly
shadowed by an action-tape seed was separated; root RNG and sampled worlds were
already seeded correctly. Conditional action evaluation is reference betting plus
native terminal rank, while paired root evaluation is fully native State.
All four stage gates failed; stop/no expansion. See README.md for measured results.

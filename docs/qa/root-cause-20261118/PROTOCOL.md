# Root-cause isolation, fixed before experiments
Source c0ca9f2058f05b21c832695034efad0445e4ff25; preserve all old checkpoints.
Scope C only, no app/UI/DB/registry/specification changes. HU50 research unchanged.

1. New six-card blind poker oracle (three ranks/two suits, one private card each,
no board) has fold/limp/3BB open, BB check/call/3BB raise/10BB3bet and SB responses.
It is a restricted diagnostic GAME, not native HU50 or a release strategy.
Independent chip-ledger settlement, exact card removal and exhaustive posterior
sums must match tree EV, CF regrets/average expectation, hidden-card-respecting BR.
Existing general_updates is reused for OS. External sampling and full exact CFR
are compared on this finite game only: 3seeds, each1sec / max100000pairs,
simultaneous updates, identical initial rows and payoff units. Save snapshots.
Success: reproducible lower exact NashConv under equal wall time, not just EV.
No automatic transfer of restricted-game results to HU50 qualification.

2. Full native frozen combined checkpoint: 4 factorial profiles (both learned,
only SB learned, only BB learned, both uniform), same8192deals/tapes, <=60sec.
Uniform ablation changes learned rows only; unseen rows stay uniform-all-legal.
No fold completion, no unmeasured all-action BR upper. Track untrained-average
visits, first-untrained partition, exact root card coverage and paired profileEV.
8 simultaneous bounded empirical-Bernstein intervals, family99.9%; no optional
stopping. Prior full169 intervals26.528742BB and old native findings are reused.
New policy candidate may expand ONLY if paired native lower improvement>.1BB.
Ablations are causal diagnostics, not candidates for adoption or normal registry.

3. Inspect frozen sampling tails with1024paths, <=15sec, no R/S updates. Record
per-path maximum regret and average weight, not a convergence bound or globalESS.
Total compute cap180sec, disk10MiB, checkpoints each completed study. If correctness
fails, stop training and fix minimal defect; if no full-native gate, no expansion.
No successful CI/old QA manual reruns; add only new regression suite to automaticCI.

Stage2 declared AFTER root-cause measurements, BEFORE native learning:
finite external beat outcome exact NashConv on all3seeds. Native untrained-S
paths99.13%, rootS145/169, very large importance increments. Test external
sampling at ONLY the first traverser decision (all legal actions), then existing
full-support outcome/control-variate sampling. This avoids unbounded full-tree
branching. 3seeds x2methods, each3sec/max1024pairs; checkpoint each complete pair.
Never retain an incomplete pair or label incomplete experiments qualified.
Independent exhaustive finite-game adapter must match CF/average expectation.
Native holdout7profiles (6trained+frozen),8192worlds, seed17118038, <=60sec.
13simultaneous intervals (7means+3external/control+3external/frozen),99.9%.
Advance only if all3 external/control AND external/frozen improvement lower>.1BB,
and fold-gain upper lower by>.1BB. Otherwise stop. No full169 reevaluation unless
this native gate passes; reuse existing width26.528742BB as unchanged evidence.
Total compute budget extended BEFORE execution to240sec, storage20MiB. This
extension is for bounded first-decision enumeration, not all-population training.

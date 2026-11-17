# HU50 convergence improvement gate (isolated research)

Starting cd78b228 checkpoint is immutable and reused, never overwritten. No
formal specs changed. Compare exact raw key / exact global-suit-orbit key, with
zero baseline / known fold-payoff control variate. No rank, size or history
abstraction. Pool old R/S only under explicit suit-isomorphism migration, record
source digest; this is a new policy, not the unchanged old policy.

Before training: prove expected CF gradient and average matching with independent
matched-history oracle; demonstrate real same-infoset repeated R/S updates and
checkpoint resume. Fold baseline known from public paid chips; every sampled
value uses inverse-probability correction. Updates delayed until path completed.
External sampling considered: full branching at each owner node with99root
choices recursively is incompatible with this short bounded gate; do not prune.

Budgets: four warm-start arms, each2seconds training and max512paired iterations;
fixed frozen-policy variance diagnostic512owner paths per arm max5seconds;
evaluation4worlds/class, all169/all99+93actions per retained comparison policy,
each<=90seconds. Total local compute<=5minutes; storage<=20MiB compressed.
Checkpoint every32iterations and stop;512decision path cap. No broad expansion
unless reproducible update-variance/coverage improvement AND held-out EV/feasible
response evidence improves within budget. Full optimized BR/NashConv unknown
remains unknown; DO NOT substitute physical100BB bound. No GTO admission.

Use identical seeds, time limits, sampler/exploration and evaluation budgets.
Report completed paths/time, so equal wall budgets aren't confused with equal
sample counts. Compare predeclared raw vs canonical+CV, keep ablations; no winner
selection using evaluation data. EV interval baseline uses previous4-world
Hoeffding method; separately report variance of unbiased CF estimators. They are
different uncertainties and must not be conflated. No claim of full convergence.

Amendment after fold-CV diagnostic: seed replication is inconsistent; do not
expand fold-CV. Add first-owner external sampling (not recursive full external):
enumerate every legal action at the first traverser node, outcome sample below.
Freeze policy through the entire batch; combine updates before applying. Average
weight for first node divided by action count, root q=1; downstream importance
correction preserved. Budget2seconds/max1024terminal rollouts, checkpoint every
64leaves, stop BEFORE any batch that would exceed leaves. No truncated action
list. Compare with existing raw-zero arm's2seconds/max1024leaves. Evaluate this
new arm with the same4worlds/all169/actions protocol; do not select a winner from
point estimates whose intervals overlap. Retain all failed CV and EV results.

RNG correction: initial external batches rewound the master stream for branch
replays, potentially reusing branch uniforms in the next deal. Superseded external
results/source are retained at276765ad075fb8b21fa7bbb0754a65538aacd8fe. Corrected
implementation samples the pre-owner prefix once and uses separate seeded branch
RNGs; master deal stream never rewinds. Regression varies branch draw counts and
proves identical master continuation. External checkpoint/EV rerun; other arms
unchanged. Prior receipts bind their historical source commit, not modified files.

Additional fixed native-only stop probe (announced before compute): three frozen
policy digests,8192iid root worlds each,<=30s/policy, output<1MiB. Compare exact
legal SB-fold payoff-0.5BB to sampled native profile EV; no Python betting/model.
Use familywise99.9% Hoeffding across3profile means, payoff range[-50,50] ONLY for
interval calculation. Completed fixed-n runs only; time-limited partial runs get
no interval. This yields feasibleBR/NashConv LOWER bounds, never upper/point
substitution. It reallocates measurement budget to root profile, not all169/action
precision or demonstrated solver improvement. No training or expansion.

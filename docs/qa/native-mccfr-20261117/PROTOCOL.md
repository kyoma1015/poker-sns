# Native HU50 outcome-sampling solver, bounded gate protocol and amendments

Evaluation-only HU50 equal stacks, chip0.5BB, zero ante/rake, full52-card deck,
all native legal actions/all streets. Not formal approval of A/B/C.
Reuse native/reference transitions, PublicResponse observations, matched-history
regret matching. Outcome-sampling MCCFR: exploration0.6 for traverser only,
opponent target distribution; alternating owners. Target policy frozen per path.
All unvisited exact information sets use a generative uniform prior over EVERY
legal action, not default fold or nearest-size alias. This defines a complete
behavioral policy but does not mean its unvisited rows have been learned.

Budget: training256 paired iterations, <=30 seconds; evaluation all169 classes,
all root actions for RFI and BB versus source3BB open, 4 worlds/class,
<=90 seconds; storage<=20MiB; checkpoint every32 iterations. No population sweep.
Time limit may stop earlier; checkpoint must contain actual iteration and RNG.
Resume must reproduce uninterrupted state exactly. No policy update during eval.
Independent native replay on seeded paths including3BB open/10BB3bet/short allin.

Measure all169/action EV on common worlds (uniform own-class combos and compatible
opponent/runout cards), baseline EV, one-decision feasible response values.
vsopen uses exact source3BB-open reach and card-removal BB-class masses,
with rejection sampling within each class. Conditional gain is scaled by open
reach when interpreted at root. It is not full root NashConv.
An initial uniform-range forced-open pilot was excluded from the final target
measurement because it is not the source policy posterior. Finite action EV maxima have selection bias and are
not full BR. Full BR/NashConv point estimates remain UNKNOWN; report only valid
trivial payoff upper bounds separately. Full-continuation evaluation uses actual
showdown/settlement, so no surrogate continuation-model error is introduced;
sampling/optimization error remains. Uniform error to true conditional EV is
bounded only trivially by payoff range until sufficient precision is established.
All169 class/action intervals use union-bound Hoeffding, confidence99.9%; never
label four-world precision as PASS. No candidate/registry promotion absent all gates.

Amendments during implementation: original budget note proposed2worlds/class;
changed to4 (2fit/2independent holdout) before the first EV evaluation so that
selected pure actions are not evaluated on their selection samples. Early
uniform-range vsopen pilot replaced by exact source posterior for the final
measurement. No significance/quality threshold was relaxed; every run remained
BLOCKED and no failed result was admitted. Code-refactor/source-pin reruns occurred
within the same short bounds, not additional population learning.

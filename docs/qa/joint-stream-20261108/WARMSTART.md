# Additional optimization trial, registered before warm training

Uniform full-population epochs1/2 have already been observed to have NashConv
7.945002/5.582644BB versus frozen profile0.932107BB. This is an explicitly
POST-OBSERVATION optimization trial, not a blind holdout or new unseen-board test.
The uniform registered4epoch result is retained irrespective of this trial.

Reuse the identical game/cache/chance, all1755orbits, shared preflop CFR and exact
independent BR. Initialize each regret entry to1e-15 times the immutable frozen
small-profile action probability; average sums start0. Thus first regret-matched
strategy is the frozen behavioral policy, while cumulative true counterfactual
regrets thereafter update normally. No opponent hidden-card features are added.
All initial regrets are nonnegative, so the positive cumulative-regret upper
bound remains conservative: each true cumulative regret <= stored regret.
Record sum of all positive initialization entries as a conservative prior budget.

Target completed warm epoch2, full-population evaluation, total invocation budget
3600seconds with atomic resume. If budget interrupts, preserve cursor; do not
evaluate a partial epoch. No candidate is promoted, and no formal acceptance is
changed by this comparison. Report worsening, target0.1BB failure and real-game
approximation UNKNOWN honestly. No further warm budget chosen from its result
in this registered trial. No additional resources/billing changes.

# Independent exact toy BR metric — before implementation

Existing smoke checks finite normalized policies but has no reusable exact BR
metric. An isolated audit measured identical, nonmonotonic matching-pennies gaps
across three native implementations; none proves poker convergence.

Add only gto/convergence.py, exposing matching_pennies_metrics(policy0, policy1).
The game is fixed: P0 receives +1 for equal actions, -1 otherwise; P1 is zero-sum.
Inputs are list/tuple length2 of finite int/float probabilities (not bool), each
in [0,1], summing to1 within absolute tolerance1e-12 with zero relative tolerance.
Do not silently normalize or mutate input. Invalid input raises ValueError.
Return game, utility_p0/p1, best_response_p0/p1, nash_conv (sum of BR improvements),
exploitability (half the gap). strategy_convergence_proof and
historical_baseline_used must always be False. No claimed poker BR evaluator.

Fixed7 new tests include25 independently enumerated payoff-matrix profiles,
equilibrium/pure controls and invalid inputs; existing29 oracle/rank7/budget
acceptance remain. Python stdlib only. No native build/DB/original checkpoint.
This independent component must not change settlement/solver/reference behavior.

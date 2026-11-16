# Preregistered actual-action-tree miniature audit

Before new measurements: reuse unchanged joint_stream/joint_vector and the actual
270-node HU50 action tree, including limp/raise2.5/3bet9/4bet21/shove50 (node112).
Only two SB hands Ac9d/Ac8d and two BB hands KhKs/QhQs, two public flops
2c3d7h and4c5d6h; exact enumeration of all990 compatible turn/river pairs.
Private deals are uniform over these four legal combinations. Board weights
(.5,.5) and(.25,.75) are two explicit finite games, NOT the full-deck distribution.
Postflop action abstraction is unchanged. Future boards excluded from preflop keys.

Compare native CF-vector gradients/own-average mass to independent Python path
products, and independently extract legal pure responses and realize their EVs.
Use genuine CFR+ alternating/linear-average teacher histories4 and32 iterations.
Each continuation inherits identical R/S/t; no invented frozen-history initialization.
Fixed additional budgets32 and128. Compare vanilla simultaneous/uniform-average,
CFR+ alternating/linear-average and DCFR simultaneous (alpha1.5,beta0,gamma2).
DCFR: R=(R+g)*t^exponent/(t^exponent+1) by sign; S=(S+a)*(t/(t+1))^2.
CFR+ each owner clips only after that owner's complete game gradient aggregation.
Average weights vanilla1, CFR+ t. No retrospective best checkpoint/mixture selection.

Improvement gate: at final128, one method must beat both initial teacher NC and
matched CFR+ continuation by >=10% in ALL four game/teacher cohorts. Gate only
qualifies follow-up SMALL-game work; never population adoption or comparison to
0.9321071527220774BB. Historical frozen policy database is not available here.
No full-population learning regardless of small success in this batch.

Estimate: <3min, <128MiB state/artifacts; hard run budget180s,2GiB free-space floor.
Checkpoint after every32 iterations per candidate, atomic JSON replace, R/S/t and
game/source/protocol identity; an explicit process is required to resume.
Normal GTO additions0; formal acceptance0/12; external GTO/real-game error unknown.

Averaging semantics clarification before final qualification: inherited teacher S
has linear weights. It is retained byte-for-byte on fork; vanilla weights only NEW
mass uniformly, and DCFR discounts the inherited mass as well. These are explicitly
inherited-history continuation variants, not textbook all-history reweighting.

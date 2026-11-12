# Legal pure BR: measured result and limits

The frozen profile remains protected; this batch extracts unilateral responses,
not a new CFR training history or a self-play equilibrium. Preflop action choices
are made only AFTER summing all1755 suit-orbit contributions/22100 physical flops.
Flop choices use own private signal, observed board and public action history.
Opponent private cards enter only the integrated chance/payoff, never action keys.

## Frozen profile, actual complete measurement

Fresh original world-enumeration BR versus extracted-vector BR, then actual pure
SB response versus original BB and original SB versus pure BB response:

- Baseline SB EV0.030880258444870145BB.
- Independent SB/BB gains0.49080281963036515/0.44130433309171235BB.
- Realized SB/BB gains0.4908028196303655/0.4413043330917118BB.
- Realized-versus-oracle/attribution maximum4.934941344458821e-14BB.
- Separately recomputing all42338 signed bins with math.fsum gives maximum
  4.9460435747050724e-14BB; distinct floating summation, same1e-8 criterion.
- Target-profile NashConv0.9321071527220774BB, unchanged. Criterion0.1BB UNMET.

Largest signed phase contributions: SB flop after open2.5/3bet9/call
+0.39466183319752557BB, BB at that branch+0.324485020159376BB.
Other positive/negative preflop and flop terms are retained; contributions sum
exactly to each player's root improvement, not a count of independently additive
local edits. Q4o BB fold vs4bet has BR-path contribution0.005984429139691903BB
but original-profile reach only8.596767334671165e-8 and a baseline one-info edit
gain9.032842770658365e-7BB. BR changes earlier decisions too. Off-path completion
can move attribution between earlier/later decisions without changing root NC.
See frozen-diagnostics.json for public histories, pot/SPR and own-signal aliases.

## Registered small-game controls

Eight matched cohorts: two explicit finite fixtures, actual teacher histories
3/128 updates, further budgets4/128. Nine update/averaging/street-control methods;
all64 legal pure responses enumerated independently at each checkpoint. Initial
R/S are genuinely inherited; explicitly labelled reset-R is diagnostic-only.
Street-scoped methods omit new regret updates at frozen streets but retain old
history and add actual new average mass; these are NOT standard full-game CFR.

No candidate passed the preregistered ALL-eight-cohort improvement gate. For
example delayed averaging improves longer-horizon fixtures, yet teacher128/budget4
in fixture0 cannot improve its initial0.006764418BB at all. Nonmonotonic short
updates are not proof of a bug or permanent nonconvergence. The correct decision
is to retain the frozen baseline, not repeat full-population epochs based on an
unmatched tiny-game success. New methods adopted0, new whole-learning runs0.

## Evidence and release qualification

Compressed realization certificates preserve raw original-utility evaluations,
independent BR leaf values and EVERY signed attribution bin. Short CI checks this
arithmetic/identities and replays tiny games; it does NOT rerun1755 native kernels.
Compact actual pure-policy SQLite files remain outside Git, with SHA preservation
and recovery procedures. Original5GB ZIP and source/evidence ZIP were actually
rehashed and match their ledgers; old DBs, caches, Git objects and UI are untouched.

Formal checklist read from ev-precision-20261030/ACCEPTANCE.md and
root-br-20261105/MVP_ACCEPTANCE.md:0/12 (delta0), ordinary GTO admission0.
Bounded current source search still finds missing20-stack/full-sizing references,
not the authoritative registry. Existing synthetic20-stack tests are NOT it.
MTT/ring,2–9players,positions,ante/rake requirements remain mandatory. Authorized
exact-condition external GTO comparison UNPERFORMED; numerical difference UNKNOWN.
Additional sizes,two raises,later streets,private abstraction and real-game model
error remain unresolved. No result here measures complete NLHE exploitability.

Shortest next path: use legal BR diagnostics to preregister a matched-history
candidate and first demonstrate small-game improvement; require independent root
BR improvement before a new population trial/adoption. Recover formal condition
registry and matched reference/independent richer-model validation in parallel;
only then qualify169-frequency/actionEV datasets for ordinary UI. Runtime for
release UNKNOWN; no fabricated completion percentage or delivery deadline.

# 6max / 9max parallel track — offline scope, not a released strategy

Source ac72bafd5d42a9c75f88eb28a86aec3de362466d. Full first-release scope is NOT
reduced to HU:2–9 players, positions, actual20stack requirements, legal sizes,
ante/rake and169hand actionEV remain required. None of the pending specification
choices is adopted by these research fixtures.

## Existing assets reused

- `gto.native.training.NativeGame`: already2..9 players, explicit unequal chip
  stacks, native0/1BB BBA and0/5/10% rake/caps under preserved candidate semantics.
  These allowed implementation values are not the approved release profile list.
- `gto.native.poker_oracle.exact_policy_value`: exact finite supplied-policy vector
  EV already supports2..9. Existing three-way AA/KK/QQ test covers side pots/refund.
- `gto.native.policy_rollout.policy_value`: existing bounded fixed-state2..9
  vector rollout with sampling intervals and mean rake. No new MC estimator needed.
- `belief_value/action_values` intentionally reject non-HU support. They cannot
  be relabelled6max/9max merely by extending a length2 array.
- Existing native training batches cover2..9 with genuine checkpoints, but no
  convergence/verified multiplayer strategy follows from those smoke runs.

## Minimal new offline adapter — criteria fixed before tests

New multiplayer_scope.py will bind the complete explicit game config/player count
and provider digest, provide acting-seat own cards + public ledger only, reuse
PublicResponse validation and reference Betting, and replay actual NativeState.
No implicit missing-history action, no HU-range transfer, no nearest-size alias.
No folded-player card redeal: full52permutation supplies2Nholes then the board.
All legal native sizes and postflop streets stay available.

Focused regressions, <=10sec and no training:
1.6/9 seats: exact own-card visibility, causal board visibility, legal public state.
2.6/9 unequal stacks: AA/KK/QQ all-in with folded extra seats; independently
   hand-derived three pot outcomes including unmatched refund.
3.BBA plus10% rake: vector net sum equals negative rake, not zero; ante/sidepot
   eligibility and no-flop-no-drop remain existing engine semantics.
4.Missing/illegal policy, wrong-player/config contract, invalid deck fail closed.

## Solver extension design / blockers

HU pre/post joint CFR currently has2-owner reach and two-private-type matrices;
its aggregate zero-sum NashConv/minimax interpretation is not a multiplayer
certificate.6..9 development must use per-seat utility, sidepot eligibility,
public/private joint chance with all2Ncards removed, and reach excluding each
updating owner across ALL other players. Neither product of independent HU ranges
nor pairwise equity substitution supplies that distribution.

Stages: offline vector/contract parity (this work), exact small3+player hidden-card
regret and private-information BR oracle, native6/9 same-game joint policies with
N-owner R/S and resumable chance state, then independent multiway unilateral
response/error validation and approved conditions before existingregistry/search.
External sampling may avoid fullN-private-type tensors, but must first prove
unbiased regrets and realization averages in the exact multiplayer oracle.
CFR convergence in general multiplayer/general-sum games is not guaranteed by HU
two-player zero-sum theory; measure all unilateral gains and label any restricted
response/game bounds correctly. With rake, sum utility is negative rake.

Odd-chip ordering, dead-ante eligibility, cap/rounding, unequal-stack and MTT/ICM
requirements remain formal approval/coverage dependencies. The adapter does not
invent their product requirements. All existing formal12conditions stay intact.

No solver training, registry/search write, production/DB/Storage/deploy/main/SSO/
billing/destructive operation or automatic-resume capability is added here.
Test results and changed files will be reported to the parent for integration.

## Observed implementation / focused result

Implemented `gto/qualification/multiplayer_scope.py` and
`gto/qualification/test_multiplayer_scope.py`. No old native/HU engine changed.
`OfflineProfile(game,provider,players=...,provider_digest=...)` rejects a mismatched
HU/multiplayer/config declaration and mutated game rules. `replay` consumes a
full52permutation, exposes only acting-seat own/public Observation through the
existing PublicResponse, and preserves all native/legal action sizes and streets.
It returns the entire utility vector, rake/refund/pot details and explicit UNKNOWN
BR/NashConv/infosetEV fields. Missing/illegal rows and exhausted step budgets fail
without a partial EV or invented fallback. Inputs are fixed diagnostic worlds,
not a new hidden-information chance model or solved strategy.

New6regressions PASS in0.016sec:
`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_multiplayer_scope -v`
See `multiplayer-focused-tests.txt`. The thin native binding returns integral-valued
floats; the new adapter validates finiteness/integrality before lossless conversion
to chip integers. No engine or utility formula was altered.

For BOTH6and9 players, independently hand-derived sidepot outcomes matched native
and reference settlement. Seats0/1/2 holdAA/KK/QQ, extras fold but their holecards
stay removed. Stacks10/6/2chips produce refund4 and pots6+8. AA/K/QQQ win vectors:
(+8,-6,-2),(-6,+8,-2),(+2,-6,+4), with all extra seats0. With BBante2 and10%rake,
main8+side4 and refund6 produce (7,-6,-2),(-4,5,-2),(0,-6,5), rake1 in each case;
vector sum=-1. A separate preflopfold test confirms no-flop-no-drop with BBA.
The all-seat check/call fixture also asserts all6players tie on sharedquads, and
all9active seats yield vector(-2x8,+16) when seat8quads6 beat the publicfullhouse.
These are settlement fixtures, NOT6/9GTO strategy results or independent fullBR.

No HU arrays were padded, no positional ranges generated, no formal profiles or
20stack list adopted. Verified6max/9max strategy count remains0; formal0/12 and
existing registry guards remain unchanged. Parent owns overallcommit/push/newCI.

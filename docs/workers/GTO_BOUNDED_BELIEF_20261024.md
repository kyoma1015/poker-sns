# C: bounded explicit opponent belief and immutable policy — 2026-10-24

Continuation of e8e40bf on existing codex/c-initial-chance-reach-20261023.
No new PR or CI invocation, no main/controller/host/scheduler/retained-state adoption.

## Contract

`gto/native/history_reach.py:immutable_average_policy` copies actual observed
native average rows into closed-over immutable tuples. Each response is a fresh
dict. Later solver training does not change this policy. Caller MUST provide
exclusive construction access: pre/post iteration/RNG/key checks detect ordinary
change, not an OS lock or atomic concurrent native snapshot. Missing/unvisited
rows are refused. max_rows is validated before row expansion. Probabilities are
exact normalizations of serialized binary64 values, not restored native precision.

`bounded_belief_value` supports two players, seat0 known hero cards, bounded
explicit opponent-card support, exact nonnegative Fraction priors summing to1,
and one common explicit action history. Rejects blockers, duplicate unordered
opponent hands, booleans, invalid cards, illegal history, missing policy, and
budget overflow. max_deals is checked before traversal. max_nodes is an aggregate
EV expansion budget across support. The inherited history bound is1000 actions.

Prior mass is **conditional on this caller-supplied support and hero blockers**;
we do not assert uniform/full-support deal probability. It is not multiplied by
the full private-deal chance again. Each support row records prior, public chance
reach and per-player strategy reach. Bayesian posterior uses their product.
Optional counterfactual_mass excludes only the specified actor's strategy factor;
it is a path mass, not a BR or counterfactual-value solution. Illegal public-card
histories for ANY support row are rejected, **not** silently removed and priors
renormalized; caller must explicitly supply history-consistent support.

Policy receives full native state. No hidden-card information-set consistency is
asserted: this is an explicit full-state-policy oracle conditioned on finite
belief, not full-poker/infoset EV. Zero evidence -> posterior/EV null. Unknown
policy -> explicit refusal. native_infoset_ev and hand169_ev remain null.

## Actual native proof and QA

13 new methods per separate Next/Cache/Packed process =39 new PASS. Preserved
old232 regression cases all PASS: total271, FAIL0. runs.json holds exact commands
and all exits; protected.json byte-compares19 preexisting test files to input.
(Count may include handoff test files; use the JSON as exact source of truth.)

Known-card river proof: hero[0,5], opponentAA[48,49] prior1/4 or QK[40,45] prior3/4,
board[1,8,17,26,35], check/call policy. Native terminal values are[-2,+2] and
[+2,-2]; exact conditional average[+1,-1]. Public chance mass1/(48*47*46*45*44),
posterior remains[1/4,3/4]. Independent arithmetic uses Fraction.
A separate fold observation with strategy1/4 vs1/2 yields evidence7/16,
posterior[1/7,6/7], while actor0-excluded path mass is1. All3 native variants pass.
Checkpoint uninterrupted4000 vs split2000+2000 yields same RNG and immutable
policy row. Later training cannot mutate snapshot returned dictionaries.

Fixed preimplementation import FAIL is before-import.txt (missing new API;
0methods executed). The first showdown fixture mistakenly used cards[12,21],
which actually complete a straight; its failed expectation is retained in
fixture-straight-error.txt and initial-runs.json. Corrected fixture uses QK;
no evaluator, old test, source legality check or pass condition was weakened.
An earlier newly authored free-check fold was illegal; fixed test instead uses
zero-reach legal check history. This is fixture correction, not a solver bug fix.

The existing workflow_dispatch workflow includes the new tests for future
owner-authorized runs. It was NOT invoked. Local test logs are not CI evidence.
No new original artifact, G11 checkpoint or source recovery is claimed.

## Remaining

Complete opponent/public chance enumeration and authentic information-set belief
provenance; observation abstraction/strategy consistency; native169/action EV;
immutable checkpoint snapshot synchronization; formal20stacks/full sizing/model
validation; originalG9/G11 ABI/history checkpoint and real-poker convergence.
Next task: bounded public observation-conditioned support constructor with exact
mass accounting and explicit hero information-set consistency checks; test it
against hand-derived river cases before any169EV export.

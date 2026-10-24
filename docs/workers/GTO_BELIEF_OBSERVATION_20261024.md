# C: observed public cards, finite belief and queried hero consistency

Input dc900b0ea376ac9e34519f22da35c878a44d9d4d, existing
codex/c-initial-chance-reach-20261023. No new PR or CI invocation. No main,
controller/host, scheduling, retained SQLite, checkpoint originals or production
changes. Continues the previous finite history/belief EV implementation.

## New implemented contract

`gto/native/belief_observation.py:condition_public_cards` validates explicit prior
support before filtering public-card blockers. Distinct unordered opponent hands,
hero blockers, duplicate board cards, bool/range/type, exact Fraction mass1,
nonempty input and cap are checked. Outputs compatible/removed prior mass and
normalized compatible support; these masses sum exactly to1. This is finite
caller-supplied conditional support, never asserted complete or a uniform prior.
A zero compatible mass returns no fabricated distribution.

`infoset_consistent_policy` validates exact legal policy and caches canonical
probabilities at queried hero information_state_string keys. Different hidden
opponent cards cannot cause different hero policy at the same queried key.
Missing zero versus explicit zero is normalized consistently. Returned dicts are
copies. max_infosets bounds storage. Opponent strategy is not constrained; cache
is sequential, not concurrent synchronization. This is only a queried-node check,
not proof that an entire unseen policy is measurable at every information set.

`evaluate_observation` connects filtering, native replay, the consistency wrapper,
and the previous bounded belief oracle. Requires the advertised public cards to
match exactly the actual replayed board; it refuses conditioning on future cards
not revealed by history. Every surviving support receives that same legal public
history. Full observed likelihood is compatible_prior_mass times the oracle's
conditional evidence_mass. Thus private blocker removal and public draw chance
are not double counted. With no surviving support, returns EV/posterior null and
history_validated=False because no legal compatible state exists to replay.

Explicit full-state policy oracle remains a limited evaluation, not native
infoset/169hand EV or equilibrium computation. Those EV fields remain null.
No changes to old history_reach API semantics or old tests.

## Actual QA evidence

Local310PASS/0FAIL = previous271 preserved +13new methods ×3separate native
variant processes. runs.json lists exact commands/exits/counts. protected.json
byte-checks20old test files against input. before-import.txt proves the new module
was absent before implementation (0methods executed); this is missing-contract
baseline, not a claim of an existing solver accuracy defect. New test development
caught incorrect assumed flop actor; fixture now obtains the actual native actor
and legal shove, with no source/test safety-gate weakening.

Fixed examples:
- supportAA prior1/4 and QK prior3/4; public[48,8,17] removes AA only, retains3/4.
- native legal call/check/flop/shove/fold history has full evidence
  3/(4*48*47*46), conditional posterior[1].
- known river[1,8,17,26,35], no blocked support, posterior[1/4,3/4], exactEV[+1,-1]
  and evidence1/(48*47*46*45*44).
- same hero information key with hidden-card-dependent action is refused.
- allblocked support remains null, zero prior removal changes no mass.

Saved proof_runner.py was executed independently for Next/Cache/Packed. New
conditioning, river EV, filtered-history EV and hidden-card-policy refusal yield
identical canonical exact-rational SHA256:
6aa496d65461fe56d489b7d0205068ae2b56af96f088be2dda5c4bc5911e0ddd.
See docs/qa/belief-observation-20261024/*proof.json and cross-variant.json.
Existing workflow_dispatch test recipe updated only for future authorized runs;
local310PASS is not a CI success claim. New PR/manual CI forbidden and not done.

## Remaining / next

No complete originalG9/G11 compatibility or real-poker convergence evidence.
Complete support enumeration, policy measurability outside queried states,
observation likelihood under opponent strategy, and authentic169EV remain gates.
Next safe component: exact finite infoset-action value comparison sharing the
same public observation across hero actions; preserve explicit support provenance,
hero consistency, zero-evidence null and aggregate resource bounds. Independent
small river oracle must precede any aggregation/export claim.

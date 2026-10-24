# C cycle3: finite common-hero decision action comparison

Starts4fd276bb4ed23f1d4ea02ba1b81855ffcf87f932 on existing
codex/c-initial-chance-reach-20261023, after root preserved the previous local and
GitHub histories. No new PR, manual CI, main/controller/host/scheduler/retained-state
or production adoption. This continues exact finite belief evaluation.

## Implemented, narrowly stated contract

`gto/native/belief_observation.py:compare_hero_actions` conditions explicit card
support on the actual public observation, then replays one common prefix. Every
surviving support must reach the SAME native hero information_state_string and
legal-action list, at a nonterminal/nonchance seat0 decision. Board must match the
advertised observation. Only caller-selected unique bounded legal integer actions
are evaluated. Wrong actor, terminal, chance, invalid action and inconsistent
prefix are refused; policy missing/illegal or queried hero-key inconsistency
remains fail-closed through the previous wrapper.

The observed prefix posterior is calculated ONCE and shared across all hero
interventions. Each selected action is forced, then the explicit pure/deterministic
continuation policy is evaluated on actual native states with the existing exact
Fraction oracle. Target policy probability is NOT multiplied into a do-action
value. One max_nodes budget covers all actions × support, not each separately.
Action row node counts and total are returned. max_actions, max_deals, history and
infoset-cache bounds remain finite. Native legal enumeration retains its own
inherited native guard; this is not support for arbitrarily huge action spaces.

Observed posterior includes actual prefix strategy reach. Separately reported
hero_counterfactual_mass excludes hero's prefix strategy only, and is NOT used as
an observed posterior or CFR value. Zero observed prefix -> selected action EVs
null; excluded-hero mass can still be positive. Empty compatible support returns
null with history_validated=False. Full original-support probability is retained
through compatible prior mass and explicit observation evidence.

This is a finite conditional explicit-policy action comparison at a shared hero
information set, NOT solved native infoset EV, full169EV, equilibrium or best
response. native_infoset_ev and hand169_ev remain null. Query-only hero policy
consistency does not prove policy correctness on unqueried states. Opponent
policy remains an explicit supplied strategy, not an inferred optimal opponent.

## Fixed exact oracle and actual native measurements

Known river hero[0,5], board[1,8,17,26,35], opponentAA[48,49] prior1/4 or
QK[40,45] prior3/4; shared legal hero actions[1check,4allin]. Under opponent
fold-to-bet continuation, checkEV[+1,-1], shoveEV[+2,-2]. Under a second prior
AA3/4/QK1/4 and opponent call continuation, checkEV[-1,+1], shoveEV[-2,+2].
These derive from native integer terminal payoffs and exact weighted arithmetic.
Observed chance mass1/(48*47*46*45*44). Action comparison does not weight values
by target action policy; a zero-policy check action is still evaluated.

13new methods ×3 separate native variant processes =39PASS. Old310 preserved:
local349PASS/0FAIL. Existing21test-file blobs match input; no protected test
weakening. Exact aggregate budget6 succeeds and5 refuses, action order gives
same value map. Initial missing-API import failure is in before-import.txt:
0methods executed, an unimplemented-contract baseline, not a claimed old solver
accuracy defect. Native modules were reused, no dependency installation/build.

Saved proof_runner.py runs new action comparisons and zero-reach cases independently
for Next/Cache/Packed. All three canonical exact-rational output hashes match:
f1b15935a096438e939b8138457033aed422b508553f2e2b93cfcad8ce00e1c5.
See docs/qa/infoset-actions-20261024/runs.json, protected.json, *proof.json and
cross-variant.json. Workflow_dispatch test recipe updated only; no manual CI run
started and local tests do not establish GitHub CI success.

## Next / unresolved

Before any169EV export: authenticated source of complete belief support, authentic
reach conditioning, game/profile/config identity, aggregation across ordered
hero combinations without double-counting, and explicit policy/coverage evidence.
Next finite step: construct a provenance-carrying action-value record per hero
combination with strict same-observation/config/policy identity, then exact
coverage-aware aggregation with missing-hand EV null. Do not reinterpret partial
support as a solved full-poker strategy. OriginalG9/G11 ABI/checkpoint compatibility,
20stack/full sizing validation and real-poker convergence remain unproved.

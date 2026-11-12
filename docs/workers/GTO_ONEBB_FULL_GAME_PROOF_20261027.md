# Explicit HU1BB complete-game statistical certificate

This is a separately labelled validation condition, NOT an ordinary RFI open,
vs-open or vs3bet range and NOT an authoritative20-stack/sizing specification.
The initial release targets remain unchanged. No postflop action is artificially
removed. No claim that the100000iteration native average has converged is made.

## Actual game and complete strategic scope

Use unchanged hash-verified NativeState/Ledger with stacks[2,2]chips, BB2, SB1,
no ante/rake, full52-card deck, no fixture/root prefix. BB posts its entire stack.
SB has1chip left; its full legal action set is exactly0(fold),1(call). Raising
cannot create a side bet against an opponent with no remaining chips. Fold ends
the game with net[-1,+1]chips, i.e. SB value-0.5BB. Calling commits the last chip;
both stacks are empty. Every later node is an actual native card-chance node,
until a genuine five-card board and original seven-card evaluator/settlement.
No later strategic player decision exists. Helper throws if any is encountered.

For an SB information set h, let C(h) be its call value in BB. The only possible
unilateral improvement of always-call is max(0,-0.5-C(h)). BB has no action, so
its deviation gain is0. A simultaneous lower bound L(h)>-0.5 for ALL information
sets therefore proves whole-game max unilateral gain0 on that coverage event.
This is why the following method is global for THIS game. The same inference
would be invalid for ordinary RFI/3bet games with later player decisions.

## Card coverage and symmetry

There are2652ordered SB hands,1326unordered combinations and169rank/suit classes.
Global suit permutations and reversal of a player's two private cards preserve
the native evaluator: ranks use card/4+2, suits only equality, seven-card scoring
maximizes over five-card subsets. Uniform remaining-card chance is invariant
under these bijections. Thus the6pair,4suited or12offsuit physical combinations
per class have equal C(h); both own-card orders do too. We sample169canonical
representatives, not1326independent hero combinations, and explicitly disclose
the exact orbit expansion. Standard native tests compare suit permutations,
own-card reversal and player exchange with native settlement on real deals.

Each trial draws both opponent cards and all five public cards uniformly
without replacement from the remaining native deck. The helper reuses original
State::apply and settlement and checks root legality, absence of later decisions,
integer win/loss/tie outcomes and chip conservation on EVERY trial.

## Statistical guarantee, distinct from exact equity

Per class, call payoff X is in[-1,+1]BB. For n=10000independent uniform trials,
use r=2sqrt(log(2*169/delta)/(2n)), delta=1/1000000000. Two-sided Hoeffding and
a169class union bound give simultaneous coverage at least1-delta. Means are
exact rational(wins-losses)/n before float display. Interval endpoints round
outwards. These are confidence intervals, NOT deterministic exact-equity bounds;
the frequentist guarantee assumes the stated independent-uniform sampling model.
Implementation uses a fixed reproducible mt19937_64 pseudorandom stream and
unbiased uniform integer draws; no claim of cryptographic randomness is made.

Fixed top-level seeds17and29 were specified before calculation, each with169
class streams and10000trials/class. Both must independently pass every-class
dominance. Joint coverage is at least1-2delta=99.9999998%. On that event the
always-call profile is globally optimal for this complete game. Source hashes,
raw counts, sample/seed plan, all derived means/bounds and source model must
recompute before the UI entry can be generated. An unverified boolean cannot
create a range. This is a statistical certificate, not an unconditional symbolic
proof that sampling error can never occur.

The ex-ante always-call value is exactly[0,0]BB by exchanging the two uniformly
dealt player hands: both invest2chips, pot4has no rake/odd-chip asymmetry, and
the payoff changes sign. Its weighted169sample estimate must contain0in the
aggregate conservative confidence interval. Independent card-ranking correctness
continues to depend on the original evaluator and its numerical oracle tests;
sharing the original implementation is not a separate evaluator implementation.

## Witnessed calculation

Source head53864b708ef0aad5eca651b99aaf242e276607a6, CI40458659464,
job122037805790 SUCCESS.3380000terminal evaluations. Both seeds passed all169
classes; minimum(lower call EV - fold EV)=0.07433531481927685BB. Raw evidence
SHA256af9aac9f8eaf3d2d0f103fc156bd3883daf23ec5b508c3d471b01838f0289d62
(excluding trailing newline). NativeState/rules/helper hashes are in the raw
evidence and verified against source by onebb_release.py.

Actual native learned-average whole-game gain intervals, same game and seed17:
-2000iterations:updated1402/2652, gain[0.1033921594,0.7385067062]BB.
-20000iterations:updated2650/2652, gain[0.1147913435,0.1591677229]BB.
-100000iterations:updated2652/2652, gain[0.0453608302,0.0653149216]BB.
These averages are NOT certified as zero-gap GTO. Missing/updater-zero rows get
worst-case bounds; native initializer pseudocounts are not considered learning.
The released test profile comes from the complete-game action-dominance
improvement, not a false relabelling of these learned averages as converged.

Ordinary HU100/100chip test contexts RFI/vs-open/vs3bet were separately trained
at200/2000iterations. RFI obtained an observed target policy at2000; facing-open
target and facing3betprefix remained unobserved. Their global convergence is
UNKNOWN and no such range is released. This minimal whole-game reference is
a calibration and a usable explicitly labelled special case, not completion of
the requested ordinary preflop release or the formal12acceptance items.

Recompute:
`python3 -B -m gto.native.onebb_release --evidence docs/qa/full-game-calibration-20261027/onebb-evidence.json --check src/gto/oneBBRange.ts`

Reexecute actual experiment after pinned native reconstruction:
`python3 -B -m gto.native.onebb_certificate --runtime FRESH_BUILD --output FRESH_EVIDENCE`
Native CI reruns the full experiment and compares the frozen raw evidence hash.

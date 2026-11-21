# Same-game joint preflop/continuation CFR — release BLOCKED

Baseline fbdd08327e029f07da22957cc43adf696d335e9e. Reuse protected joint_vector
kernel, existing joint_update_audit/joint_history games, native betting and rank
engines. New Trainer jointly updates preflop and continuation regrets and genuine
linear own-reach averages in ONE fixed game. Shared preflop gradients integrate
all public outcomes BEFORE updating/maximizing. Public continuation states update
with the same current profile; exported average is exactly that game's policy.
No old-range fixed payoff/new-range runtime resolver switch. No old solver/store
modified, no fabricated inherited regrets. Old full-population failures preserved.

## Exact gate (complete pure BR enumeration)

Two existing games,2private types/2public outcomes,64pure strategies/player:

|iterations|game0 NashConv BB|game1 NashConv BB|
|---|---:|---:|
|0|1.124375|1.383125|
|16|.017462681|.019952863|
|64|.002502403|.001532289|
|256|.000242264|.000148979|
|1024|.000040993|.000035745|

Both gatesPASS. Direct cashflow polynomial/all64pure BRs agree with CF-vector;
per-action regret/average/denominator agrees with independent path oracle;
independent alternating teacher and realR/S resume agree. Preflop cannot observe
future public bucket or postflop private signal. Bayes opponent posterior matches
current action/chance reach. This is exact finite-game convergence, not HU50 proof.

## HU50 bounded transplant

Native3/10/50BB preflop tree, including limps and all modeled call branches;
flop native-legal check/halfpot/jam tree; turn/river check-through. Public paired/
unpaired bucket, private169class plus current made-pair/fourflush flag. Own cards,
visible board/history only; no actual opponent/future card input. All modeled
cashflows/selected sizes verified against original native State for wins/losses/
ties; shortallin legal response and source/build identity guards tested.

Each sampled flop enumerates ALL1,271,256 compatible ordered physical hole pairs
and ALL990future runouts/pair, using protected fast rank-cache code. Card removal
exact; conditional moment mass normalized and seat-swap equities conserve value.
Pair/trips board prior3796/22100; unpaired18304/22100. Two train and two heldout
flops/seed; preflop private prior across these sampled flops is a FINITE-MODEL
prior, not an exact full-population card distribution. Flop/bucket/private/future
abstraction and board sampling errors UNKNOWN. Zero runout sampling within a flop
does not imply zero whole-game sampling/model error.

|seed|train NC 0/16/64/128|heldout NC 0/16/64/128|oldB heldout NC|
|---|---|---|---:|
|17119201|9.017558/.369561/.066208/.020859|8.745424/3.301009/3.441979/3.464242|17.037454|
|17119202|7.613419/.258451/.043127/.013372|9.286465/4.799551/5.105993/5.029725|17.970489|

All values restricted conditional finite games, same chance/actions for oldB vs
new. Not comparable to historical whole-population .932107 or prior .744173.
Train improves, but heldout improvement stalls after16 and a large gap remains.
Do not simply increase inner iterations.128training took12.502719/12.086360sec;
fixed-flop matrices~1.2-1.3sec each. No256extension: native pilot gateFAIL.
Self-play SB EV increase alone is not an equilibrium-quality criterion; full BR/
error bounds and heldout gaps remain the relevant blockers.

Both seeds export RFI/vsopen/vs3bet ALL169rows and every native legal action id,
selected-action conditional train/heldout model EV, and matching policy digest.
All169preflop rows have genuine positive average mass. Postflop remains sparse:
on unpaired heldout board78/55private signals absent from respective train board;
zero-average rows use explicit uniform model extension. They are not verified
continuations. Unknown preflop sizes use protected exact-history fallback; unknown
flop history and turn/river use explicit check/call, never missing-history fold.
Native all169/alllegal action EV confidence intervals remain UNKNOWN.

## Independent native holdout and residual exploit

Fresh seed17119211, fixed2048worlds,22,528native paths,58.125sec (<120s).
OldB, previous Range reoptimization and2joint policies share decks/tapes.
Seven legal probes on prespecified seed1: open3.5,3bet10.5,riverjam,fold,
open2.5,3bet9,absolute river nuts jam. Original15family intervals in native.json;
river-bound.json contains revised intervals with joint99.9% allocation across
15intervals AND100CDFlevels, no extra worlds/reuse of old-policy event mass.
OldB SB EV .032958984,previous .087890625,new .161621094/-.112548828BB.
New-oldB paired +.128662109[-3.383098,3.640422] and
-.145507812[-3.736047,3.445032]BB: no significant EV difference.

Known nuts attack:524eligible queries,4positive jams; gain point.091796875BB.
At matched zero-rake river, own/public absolute nuts cannot lose to ANY compatible
opponent; fixed defender always check/calls. Jam gain is remaining stake on a
strict win,0 on a tie. No future chance remains. Native oracle exhaustively checks
all990opponent holes in a royal-nuts matched3BB pot: every jam gain47BB.
This establishes pathwise nonnegative gain for the specified attack, not merely
nonnegative observed samples. Integer chips imply half-BB gain lattice. Summing
100Clopper-Pearson survival lower bounds, Bonferroni failure.0005/100, yields
**independent native BR gain/NashConv LOWER .002359953575BB** for SAME seed1digest,
99.9% joint with revised15intervals; numerical guard1e-8. No opponent cards in
attack selection. This positive lower bound is not a complete BR upper or a claim
about an unapproved tolerance. It identifies passive turn/river as residual risk.
Other exploratory gains/intervals are saved; wide intervals do not prove safety.

Complete native BRupper/NashConv point/upper, alllegal169/action EVprecision,
uniform continuation/abstraction/omitted-size error UNKNOWN. No physical payoff
upper cap substituted as convergence evidence. Formal0/12,verifiedRFI0/3bet0,
normal registry0. Eight old research candidates remain BLOCKED_UNVERIFIED.

## Reproduce/restart/protection

99regression testsPASS (9new). Source paths/commands in workflow and tests.txt.
No local npm/build/lint/browser QA: no app/TS/UI changes. Initial pilot before
source/build guards retained under initial-pilot; receipt verifies identical pre/
post policies after deterministic source-guard replay, not independent trials.
Actual R/S checkpoints, all conditional moments, average policies and world/tape
bytes in Git. Source SHA and vector/rank binary hashes are bound. Compiled vector/
flop .so files preserved by verified move to /tmp/joint-release-{vector,matrix}-
build-20261119, NOT committed/reported as Git-recovered binaries. Rank library
/tmp/range-continuation-build/range.so. New environment must rebuild with matching
source/compiler/options and verify identity; never silently resume a new backend.

Manual resume: reconstruct Trainer with checkpoint nodes/pre_nodes/boundary/train/
weights; verify source/build/chance identity, restore actual state, step and save.
Unit resume checks bit equality. No automatic resume/daemon. Previous SQLite/cache
paths outside this workspace are absent; no old full-population DB/ZIP recovery
claimed. Original committed source/results and available recent checkpoints safe.

Next: extend joint public-information-preserving tree through turn/river, replace
passive river weakness; improve public/private signal coverage with independently
registered heldout boards before scaling. Keep future public/private observations
hidden until revealed. Require native BR/error/EVprecision bounds and formal
spec approval before certificate/registry/search admission. Formal20stack/size/
MTT-ring/ante-rake remain unapproved; isolated HU50 work can continue without them.

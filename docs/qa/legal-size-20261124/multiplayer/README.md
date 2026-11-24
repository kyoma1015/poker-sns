# Expanded finite multiplayer joint game — not6/9fullNLHE

Source d1ce78882afa9624d78cd48cdcfee3dc9f522e10. Formal acceptance0/12 and
verified multiplayer strategy count0 remain unchanged. Existing first-release
scope2–9players/positions/20approvedstacks/rake/ante/alllegal sizes is preserved;
these small chip-stack fixtures do not approve any missing formal specification.

## Minimal actual solver extension

The existing `multiplayer_joint.Joint` N-owner R/A solver and OfflineProfile are
reused. New optional `action_scope='preflop'` adds native fold/call/check and the
3BB→10BB→legalshove sequence. When an explicit target is unavailable, the menu
can include the actual legal short/fullshove; no state, raise-right or pot rule
is invented. Exact native legality remains authoritative.

A normal matched call DOES NOT become a fabricated terminal showdown: NativeState
advances through actual flop/turn/river public states. Each postflop decision has
the explicit restricted check/call action. Therefore this is **preflop joint plus
an explicit limited continuation, NOT joint fullstreet/alllegal native poker**.
Omitted sizes/postflop strategic errors remain UNKNOWN. Missing off-tree provider
observations still raise MissingResponse; no fold completion is introduced.

Default `Joint(...)` keeps the old all-in scope and existing API behavior. Changed
raw module sourceSHA deliberately changes identity. Old checkpoint identities must
be reconstructed from original Git source AND matching native binary; they are
not relabelled as compatible with this changed module. OldCP bytes remain intact.

## Genuine hidden chance / independent oracle

Four explicit52permutation worlds carry equal positive mass. First three seats
have AA/KK/QQ combinations, with low/K/Q river alternatives and another private
assignment. Folded extra-seat cards are still removed. This is an exact FOUR-WORLD
law, not the full52card population. Own/public Observation keys are checked for
all seats and causal flop/turn/river prefixes.

Independent terminal-path products do not call Joint.reach/values/br. They remove
all own prior/current probabilities for CF action values, retain future own target
probabilities and all opponents' reach, and independently accumulate realization
averages. An independent private-plan pathBR integrates hidden worlds BEFORE each
shared-infoset max. Deterministic native profile replay for both raise and call
profiles matches the same finite-game utility vectors on all four worlds.

For initial3player uniform policy, lawfulBR_bb per seat is
[2.296296,4.947531,0]. Illegal clairvoyant per-world maxima would be
[2.763889,5.294753,2.615741]. The gap is real: the chance worlds change actual
AA/KK/QQ returns while some own preflop observations remain identical.

Hand-derived native cashflow assertions include:
- UTG3BB→SB10BB→BBshortallin22chips→UTG/SBcalls:
  rawchip world payoffs [42,-22,-20],[-22,42,-20],[-22,42,-20],[-22,-18,40].
- Sole3BBopen then blindsfold: net[-1,-2,+3], unmatched refund4chips.
- With BBante2 and5%rake, contributions20/20/20+dead2=62, floor rake3:
  [39,-22,-20],[-20,37,-20],[-20,37,-20],[-20,-22,39]. Sum=-3chips.
- Preflopfolds keep no-flop-no-drop even with deadante. No HU zero-sum assumption
  is applied to the raked utility vector.

## Measured bounded pilot

Initial3player stacks[24,22,20]chips,327nodes/673infosets. Build0.1365sec; whole
3player pilot0.7736sec. Simultaneous fixed-preupdate-policy N-owner CFR+ at0/8/32:

| steps | sum restricted unilateral gains BB |
|---:|---:|
|0|7.2438271605|
|8|0.3449383313|
|32|0.0237389456|

At32, EV_bb=[-0.512505143,0.520569131,-0.008063988], per-seat restricted gains
[0.014468874,0.001206083,0.008063988]. Independent pathEV/BR max discrepancy over
the checkpoints<=3.56e-15. These are exact finite-scope measurements, not fullnative
NashConv/BR bounds or proof of multiplayer CFR convergence. Even this finite
residual is nonzero. No formal PASS follows from correctness or restricted gain
reduction.

Original6/9pilots (fourworlds, unequal stacks, BBA2/5%rake) both hit2000nodecap:
6max0.8549sec,9max1.0429sec. `results.json` preserves those failures. No incomplete
tree is evaluated/trained/exported. Whole original pilot2.6776sec, peakRSS41.57MB.
QA remains under20MiB; memory budget512MiB respected.

### Separate6max larger build probe / concrete scaling limit

Parent approved ONE additional6max attempt, saved separately in
`6max-build-probe.json`; original2000cap outcomes/checkpoint not overwritten.
20,000node/10sec constructor budget plus external12sec/RSS256MiB watchdog:
6max again INCOMPLETE at20,000nodes in9.0316sec; peakRSS74.99MB,
externalwall9.4382sec. No training or partialtree policy/BR followed.

Thus exact required total6maxnodes is UNKNOWN but **strictly >20,000**, >61times
the complete3player tree. The memory figure is partial-build RSS, not a guaranteed
completed-model allocation bound (R/A tables are allocated only after tree finish).
Do not extrapolate the observed partial memory as a whole-game certificate.

For9max with the same first6stacks/blinds/BBante, the legal branch where seats6/7/8
fold embeds every6max public action path, with the extra-fold events interleaved.
The extra seats pay no ante under these explicit BB-only-ante fixtures. Removing
these folded seats leaves the same first6 betting/raise-right states and board
worlds. Therefore9maxalso requires **>20,000nodes**, already beyond the same node
budget. A full9max build was not attempted. This lower-bound argument is a design
estimate using a legal subset; it does NOT adopt fixed-fold seats or claim a9max
strategy. Exact totalnodes/completedRSS/time for either size remain UNKNOWN.

Next implementation should replace complete-tree materialization with the existing
native/sparse external-sampling route, preserving the tested N-owner opponent
reach products, private/public keys, full-card removal and vector settlement.
A new exact3player expectation/pathBR comparison is required before6/9scale.
Raising the old complete-tree limit alone is not validated within these budgets.
Multiplayer/general-sum CFR does not inherit the HU zero-sum NE guarantee; all
unilateral gains and real-game errors still need independent validation.

## Regressions and resumption

Current new suite:
`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_multiplayer_expanded -v`
**7PASS** in0.995sec; `focused-tests.txt`.

Existing compatibility class was run because the shared Joint implementation was
changed:
`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_multiplayer_expanded gto.qualification.test_generalize.MultiJoint -v`
At that run,6new+5existing tests=**11PASS** in1.325sec; subsequent seventh new native
profile replay test alsoPASS. `compatibility-tests.txt` records that earlier run.
No successful CI was manually rerun, no old long experiments repeated.

`expanded-3max-checkpoint.json` contains actual R/A/t/actions and exact game/source/
native identities. Restore with the SAME source/binary/config/fourworlds:
`q=Joint(native,game,expanded_decks(3),[.25]*4,action_scope='preflop')` then
`q.restore(json.loads(checkpoint.read_text()))`. There is no samplingRNG in this
exact finite-world loop, and no automatic restart service. Original legacy source:
`git show d1ce78882afa9624d78cd48cdcfee3dc9f522e10:gto/qualification/multiplayer_joint.py`.
New source/artifact/legacy-source pins are recorded in manifest.json.

No commonworkflow/progress/registry/search changes were made by this parallel task.
Parent handles commit/push/newCI. Full native BR upper/NashConv/all169actionEV,
omitted-action/continuation errors and6/9verifiedstrategies remain UNKNOWN/0.
No prod/DB/Storage/main/Vercel/SSO/paid/destructive operations occurred.

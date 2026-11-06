# Continuation approximation audit connected to guarded preflop search

A0.0015BB preflop-only NashConv with frozen continuations is not a full-poker
certificate. This batch checks the missing continuation decisions using actual
published independent preflop profiles,not fabricated matrices or a new ordinary
range. Original policies/ranges/equity oracle remain unchanged.

## Controlled whole-population experiment

Four configurations: small/large preflop profiles × aftervs3betCALL/aftervs4betCALL.
Each uses exact public-history reaches,card removal,all22100physicalflops via1755
suit-orbits and all990runouts. Raw root-weighted joint M/E moments are pooled,
not equal-weight averages of normalized boardgames. Both seats' own169class×8
observable flags are retained against the other seat's8flag strategy. Opponent
actual cards enter chance/payoff integration,never action selection.

On EACH fixed range compare five controllers: originalsmall/originallarge;
refit-small/refit-large; refit-expanded. Expanded actions add0.1/0.25pot andexplicit
allin(capped10pot),union of existing1/3,1/2,3/4,1,2pot sizes,and two flop raises.
All candidates reported; no final retuning/selection. Refits512/2048/8192 use the
entire finite publictexture population and are NOT independent real-game tests or
jointpreflop/postflop CFR convergence. All96coarse games meet the research0.1BB
criterion,but that does not qualify GTO precision.

Information refinement is controlled within each fixed profile/actionset:
publictexture+3ownflags → add own169class → reveal actual publicflop. Profile EV
must stay equal and BRgain cannot decrease. Independent recursive PythonBR checks
all320coarsegames; legacy-engine agreement,an opponent-private-information
counterexample and private refinement tests cover the new native inference path.
Published CALL actionEV must match the separately computed jointmoments; root
probability error max3.47e-18. This validates cashflow/reach weights,not externalGTO.

## Measured deviation, not a real-game upper bound

Conditional-on-CALL NashConv BB on each model's own preflop ranges:

|range/stage/controller|8flags|add169class|individualflop+class|
|---|---|---|---|
|small/vs4bet/originalsmall|3.008982|3.621840|5.500481|
|large/vs4bet/originallarge|2.098835|2.577180|4.799779|
|small/vs4bet/refit-small|0.007937|1.099500|3.244178|
|large/vs4bet/refit-large|0.004824|0.542014|2.608232|
|small/vs4bet/expanded|0.008492|0.735738|2.778087|
|large/vs4bet/expanded|0.007854|1.075796|3.087952|

Different actionsets are different target games; their NashConv difference alone
is not a claim one strategy is better. Expanded actions do not eliminate the
private/public abstraction deficit. Refitting a coarse game is not fullgame GTO.

Actual restricted postflop responses at TWO disjoint CALL branches yield root
improvement gains with preflop fixed:
- small:SB0.069620054,BB0.054186882,sum0.123806936BB.
- large:SB0.058732628,BB0.082509901,sum0.141242529BB.
These are feasible deviation lower bounds in a containing game,NOT fullgameGTO
upper bounds,reference EV error or a new preflop exploitability certificate. The
branches cover2.859651%/2.839017%rootprobability respectively,not allnineCALLleaves.
The complete original nine-terminal EV computation is preserved separately.

Original perhand cross-model actionEV max7.647099BB is unchanged. Under identical
reached ranges,meanCALL-caller EV difference large-minus-small atvs4bet is
0.008365BB(smallprefloprange)/0.038492BB(largeprefloprange). These averages are not
perhand worst errors or agreement with a trusted GTO reference.

## Late streets are still unresolved

Showdown runouts are exact. Turn/river betting is NOT implemented in this audit.
Nonallin showdown probability and a conservative±50BB futurevalue envelope are
reported. Forlarge-range/vs4bet,refit-large leaves0.176210%unresolved versus
64.449087%for expanded-size profile. Its conditionalSB envelope expands from
[7.417718,7.593928]to[-36.044509,28.404578]BB. This is a safe sensitivity envelope,
NOT a measured approximation error or confidence interval. More flop sizes can
move unresolved decisions to later streets; no full-NLHE claim is made.

## Integrity, errors and UI

Preregistered protocol/source/design before fullmoment generation;localsource
commits are not external timestamp certification. FFI initially declared18args
for17argument street_train. Corrected before accepting fitted results and added
an actual training regression. Protocol/candidates/budgets stayed unchanged.
All1755moment packets were preserved and checksum/unchanged-generation AST verified
before cache metadata migration. Originaldesign/cache are retained; migration
proof is versioned. Fresh CI regenerates independently,not from migrated caches.

results.json retains all models/profiles/traces; source manifest pins inputs and
outputs. Separate lazyloaded UI presents diagnostic BR tables only for explicit
HU50 research matches. Unsupported conditions/input errors clear results. Data
cannot enter ordinary catalog and is explicitly NOT an unweighted offreach payoff
oracle. Changing preflop ranges requires correct new counterfactual evaluations;
conditional scalar/weightedmoments cannot replace them. Existing8ranges1352,
new8ranges1352,HU1BB,2–9regressions,staticdemo and frozenCFR remain protected.

Formal0/12,normalGTO additions0,externalreference acquired0/comparisons0/676permodel,
real-game approximation errorUNKNOWN. See FORMAL_ACCEPTANCE.md for all retained
requirements/source attempts. Next shortest engineering step: continuation learner
that retains own/private and public information with proper global counterfactual
reach,plus validated later-street approximation and lawful matching reference;
recover formal20stacks/fullsizes and extend qualified condition datasets. Do not
just increase an already-converged coarse game's iterations.

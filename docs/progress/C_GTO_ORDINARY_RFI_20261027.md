# Ordinary RFI priority — 2026-10-27

Input public69364245f8dd5e6d1f343f54609bbef556ee34bc, local5455f43,
identical treedc97c4125d143a7ca929a4e64350683dc4a95bbc. Both input CI
40460437415/40460437391 SUCCESS651PASS. OneBB169data/evidence/UI unchanged.
No source edits initially. No other development line/shared UI files affected.

Acceptance for this batch: use explicit ordinary HU50BB(stacks100/100chips,
BB2,SB1,noante/norake), actual full52card NativeState, all legal actions and
postflop decisions retained. Histories[],[7],[7,20],[7,20,44] correspond to RFI,
2.5BB open response,9BB3bet response,21BB4bet response. These are explicit
experimental configurations, not invented formal20stack/sizing specifications.
Train seeds17/29 at2000/20000iterations and measure all169classes/2652ordered
own-hands separately. Never aggregate partial orderings into a complete range.
Later-stage hand-frequency aggregation requires actual history posterior; no
uniform/visit weight substitution. Preserve unknown EV and no-certification.

Critical correctness finding: native rows initialize positive average pseudocounts
before the owner's first update. Existing PolicySnapshot.from_solver and the
native-average live adapter used positive average mass alone, incorrectly
allowing those rows to be treated as learned. Both now reject updater-zero rows;
regression explicitly requires created-but-not-updated rows to remain absent.
Existing positive integration fixtures now select genuinely updated rows.
Historical sources/checkpoints/oneBB evidence remain unchanged.

New full_game_bounds.py follows the complete actual continuation tree on fixed
uniformly sampled card worlds. Profile values retain pessimistic utility
intervals at unknown rows/budget cuts. Every future player decision is preserved.
For each player, maximization with revealed opponent/future cards is a
perfect-information BEST-RESPONSE UPPER RELAXATION, not a feasible strategy or
exact exploitability. Unknown opponent policies are conservatively maximized;
all-card-world expectations and simultaneous concentration are still required.
The ordinary study combines stratified within-class uniform ordered hands,
full opponent/private/board deck sampling, complete-game upper envelopes and
169class/player/metric confidence accounting. Loose bounds cannot certify GTO.
Single-world results and local EV/observed-policy drift never enable the UI.
No new special test range is added. New ranges remain gated by actual convergence.

Native runtime was lost at environment restart. Default network build failed
with PermissionError(Operation not permitted); additional network permission
request was interrupted. Do not repeatedly request it; pinned existing GitHub CI
build is the execution path, while independent source/pure checks continue.

Resume: inspect exact public head/CI; run native test_full_game_bounds.py for
Next/Cache/Packed; run ordinary_study with fresh output, inspect actual
ORDINARY_SUMMARY, fix any failing assertion without relaxing evidence. Preserve
oneBB raw evidence/generated-data check and all651baseline executions. Source
search for20stack/sizes remains unfulfilled; independent learning continues.
No production/main/billing/restart changes. AUTO-RESUME unavailable.

First publicatione88cb23f30f6069bc86482b1e4b5791ca3e5cb18:
UI40464868456 SUCCESS; native40464868619 failed1of7new native tests in
Next process. Existing preceding suites passed. Test mistakenly used preflop-only
`decision(...,[1,1])` after betting had advanced to flop chance; adapter correctly
rejected it. Fix creates the legal initial decision then applies actual actions
(1,1), retaining all real board chance/strategy checks. No production logic or
assertion weakened. Study increases to50000iterations per seed,100000total,
with2000/20000/50000checkpoints. Final169RFI frequencies and full-continuation
bounds are printed as provenance-bound JSON to preserve actual computed data.
These remain research outputs until full-game convergence is justified.

Public31707153f930ff040b85cbcc848b8d9abcb97b85: native40465148140 and
UI40465148151 SUCCESS. Ordinary50BB study,seeds17/29 up to50000each, finished;
all subsequent oneBB and historical regressions also passed. Decoded job-log
retrieval failed twice with `Transport closed`: exact rational class frequencies
created excessively large evidence lines. Do NOT infer numeric coverage from
job SUCCESS. Transport repair rounds only final exact-rational aggregates to
binary64 (explicitly labelled); no learning/bounding/model change. Rerun to recover
actual ORDINARY_SUMMARY and manageable evidence. Checkpoint hashes must retain
native identity. Original failure40464868619 remains historical evidence.

Perfect-information response envelopes may be intrinsically loose even for a
true equilibrium because they reveal hidden/future cards. A positive upper
bound is NOT proof of exploitable strategy; it only fails to certify convergence.
Two worlds/class are a readiness smoke evaluation, not an accurate169EV release.
Ordinary GTO certificate and precise169EV counts remain0until real evidence.

Witnessed decoded native40465835451/job122060900384 SUCCESS,630unittest+
25Packed=655native,UI40465835522 SUCCESS17,combined672PASS(+21vs651).
Ordinary50BB,seeds17/29,50000iterations each: RFI both2652/2652updated and
169/169complete frequency classes (also complete at20000). Vsopen updated508/462;
vs3bet3/7; vs4bet0/1. Later-stage class frequencies remain unavailable because
history-posterior weighting is not integrated. Full-game conservative gain upper
approximately100BB, providing no useful convergence certificate; ordinary GTO
range/EV counts0. Summation floating rounding observed99.99999999999976BB at
known100BB cap; repair aggregates weighted bounds as exact rationals and rounds
outwards before intersecting known utility cap. No GTO data released.

Next implementation is an explicitly separate targeted proposal module built
from the pinned original source, preserving original solver bytes and all legal
actions/postflop decisions/importance-update equations. Only native proposal
probabilities change: preflop q=0.1uniform(all legal)+0.9specified legal target
(2.5/9/21BB), then original mixture(1-epsilon)*policy+epsilon*q. Illegal target
or postflop uses original uniform proposal. Every action retains positive support
and the actual proposal probability flows through existing importance ratios.
Distinct source-specific checkpoint contract prevents original/targeted resume
confusion. This addresses actual sparse vs3bet/4bet visitation, not a game
abstraction or forced-prefix subgame. Tests check full support/normalization,
exact expectation identity over all sampled actions, all-size legality and real
postflop/native updates. Source transformation has exact hash/anchor guards.
Convergence remains UNKNOWN; larger counts alone never permit UI release.

Targeted first CI40466649170: original50BB rerun PASS and all6checkpoint SHA256
match previous successful study. Targeted C++build PASS;3proposal math/boundary
tests PASS,1native integration ERROR because separate module directory lacked
pinned pokerid_rules.py. Restore exact hash-verified adapter bytes into NEW
module directory; preserved original files unchanged. Retain native integration
assertion (all legal sizes, actual postflop and vs3bet visits). No test bypass.
Source's algorithm include placed after Python headers to avoid macro warnings.

## Resumed2026-10-28: exact HU history-conditioned169aggregation
Model capacity interruption is not a source defect. Local50966ab/public4549f5e
have identical treef3acf641c8c89ea5fc660746bf3de8d50e973f4e. Both prior workflows
40467060207/40467059999 SUCCESS; decoded native634unittest+25Packed+17UI=676PASS.
Actual targeted50000iterations,seeds17/29: vsopen2652/2652updated both;
vs3bet2648/2643;vs4bet2585/2584. Baseline same-run vsopen508/462,
vs3bet3/7,vs4bet0/1. All6original baseline checkpoint hashes match earlier runs.
No ordinary equilibrium certificate/EV/UI range was produced. Previous formal
12acceptance count0remains0; no inferred43% is asserted or incremented.

Recovered uncommitted files hu_preflop_reach.py/test_hu_preflop_reach.py,
separately backed up under/workspace; actual source status had2untracked files,
not the UI's historical5-file estimate. These files now connect to final50000
study observations. Preserve all five already-pushed continuation commits.

Reach acceptance: full HU52card model, all2652ordered own hands and2450ordered
compatible opponent hands. At public preflop history, per-player likelihood
products factor by private hand. Exact blocker inclusion-exclusion computes
compatible opponent mass, retaining own earlier-action likelihood in hero mass.
No visit/uniform/action-frequency substitution, no tiny sampled opponent subset.
Integer common-denominator aggregation avoids enormous intermediate rational
GCDs; only final normalized frequency ratios are rounded tobinary64. Missing
positive-prefix opponent factors withhold the posterior; missing target policies
withhold whole affected classes. EV staysnull and convergencefalse. Other2..9
multiway engine source and verified oneBBUI/data remain untouched.

Tests:3pure full-deck blocker/oracle/negative cases passed locally. Native suite
adds independent full2450opponent enumeration for ordered22hands using explicit
nonuniform private-hand policies in actual NativeState contexts, and actual
native partial-training missing-prefix rejection, for all3original variants.
End-to-end ordinary study will calculate reached169frequency coverage for
vsopen/vs3bet/vs4bet, preserve nullEV, and rerun existing full-tree/oneBB checks.
Do not claim new native/coverage results before exact-head CI finishes.

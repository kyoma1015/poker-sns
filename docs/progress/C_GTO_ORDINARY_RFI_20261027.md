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

# C / PR120 joint reach integration — 2026-11-07

Base public/local f7b9e54ffbdc1dde4a8fecec6018dc8d78e45b52, initially clean.
Initial engine/protocol local1269f6f committed before fitting. Existing object
alternate /workspace/poker-sns, frozen CFR, old/independent8+8 research ranges,
HU1BB,2–9regressions and static demo retained. No force/reset/clean used.

Implemented isolated joint extensive-game CFR and independent BR: own169class,
public flop/ownflags/history, unweighted card-removed chance, opponent-only CF
reach, own-realization averaging, no future-board or opponent-private action key.
All9 matched preflop branches connect; all1690 preflop rows exported per checkpoint.
11 new regression tests PASS locally, numeric/source/policy replay PASS. Build
and lint exit0; existing application chunk/TDA warnings not changed. Old protected
manifests rechecked PASS. No UI changes or ordinary GTO admissions.

Exact integration study is CONDITIONED ON3 registered known board orbits/28
physical flops,105239jointworlds,52180infosets,270nodes. NOT full-board root or
unseen generalization evidence. Same-subset frozen-small NC3.19851575339752BB,
new checkpoints16/64/256 NC1.013416650947/.378843006023/.102505673606BB.
SB/BB gains at256 .053302767680/.049202905926BB. 0.1BB target FAIL.
Future-showdown envelope[-16.295046438455,16.431716636063]BB at32.726763% mass;
outside-subset99.873303% unknown ->unconditional envelope roughly[-49.957297,
49.957470]BB. Missing actions/second raises require separate BR bounds; universal
NC<=100BB only, not the narrow restricted-game value. Previous full-population
small3.244178/large2.608232BB deviations and64.449087% unresolved conditional mass
remain unremedied; no direct cross-population improvement claim.

Formal0/12 (unchanged); PARTIAL10/BLOCKED2. Original20stack/fullsizes absent,
matched qualified external references0. New public candidate ExploitIt mismatches
ante/open/EVbasis, PokerData visible catalog not sameHUgame. ExternalGTO comparison
NOT PERFORMED, real-game approximation error UNKNOWN.

At this pre-push recording CI for new changes is PENDING. Old6SUCCESS runs have
not been manually rerun. New workflow gto-joint-reach.yml replays exact moments,
joint learning, policy fingerprints and source/protected manifests. Final public
receipt/CI results go to /workspace/joint-reach-CI-receipt.json after publication;
do not infer SUCCESS from this plan. Prior PR body update attempted but connector
rejected stale tool catalog; safe retry only, no permissions/security changes.

Resume:
1. git status --short;git rev-parse HEAD; inspect /workspace/joint-reach-*.json/log.
2. Preserve local commits, publish normal expected-parent FF to PR120, verify
   new-head CI and repair observed failures. Do not rerun successful old CI.
3. Implement full1755orbit streamed chance sweeps sharing preflop infosets; full
   information BR must integrate chance before preflop maximization. Current
   explicit-world solver is an exact small-population reference, not the final
   full-population implementation; avoid memory-unbounded world*node expansion.
4. Expand/calibrate legal actions/streets and qualify approximations against lawful
   matched reference. Recover authoritative conditions, generate required datasets,
   admit only certified rows to ordinary UI. Do not waive any formal condition.

Files: gto/abstract/joint_reach{.py,.cc,_study.py},tests/test_joint_reach.py,
.github/workflows/gto-joint-reach.yml,docs/qa/joint-reach-20261107/.
Workspace raw complete policy/evidence /workspace/joint-reach-publish.json,
cache /workspace/joint-reach-cache, build /workspace/joint-reach-build.
No AUTO-RESUME/independent restart installed. No production DB/Storage/Vercel,
main/otherPR/SSO/billing changes. No owner decision required for next safe step.

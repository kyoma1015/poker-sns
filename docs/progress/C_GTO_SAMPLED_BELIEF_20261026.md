# Sampled explicit-belief EV continuation

Input public HEAD9427f6bf3c57c9f90a64c8c4ca31762489a83360 / local8597439,
identical tested tree8b7c2993f6d3391bc64c3c0c81feda7d2fff1ff6. Existing CI
40351061844 SUCCESS. No uncommitted input changes discarded.

Acceptance: reuse native state/chance/strategy/reach validation; no full-card
enumeration for continuation; preserve exact prefix posterior; exclude target
action's policy probability from intervention values; fail on missing learned
rows and omniscient queried hero policy; report sampled uncertainty separately
from strategic convergence. No approximation of a call as immediate showdown.

Changes relative to input:
- `belief_value`: exact blocker/public-history conditioning and strategy reach
  reweight explicit opponent support, then bounded native-policy rollout per
  positive posterior deal. Rational sample means and posterior; sample/rake
  conservation; simultaneous confidence over deals and players. Aggregate
  interval bounds accumulate with rational weights and outward float rounding.
- `action_values`: compare up to64 legal common-hero interventions using the
  same prefix belief, with shared confidence budget over actions/deals/players.
  Four-bet response fold/call/re-raise exercised. No target policy-probability
  multiplication; no invented missing policy. Aggregate sample budget enforced.
- Rollout suite4→15 methods (+11), separately Next/Cache/Packed12→45 executions
  (+33). Existing four tests retained. New tests include hand-derived mixed
  river EV0 (fold-2 with3/4,call+6 with1/4), confidence width halving for4x
  samples, actual learned snapshot missing-row rejection, callback mutation,
  posterior1/4:3/4 from action likelihood, zero-reach null output, real preflop
  to postflop continuation, and four-bet response action comparison.

Evidence: `docs/qa/preflop-belief-20261026/`. Same seeded four-bet action report
across3variants SHA256d99fb126624dafeb1a8d017f5d6ca4d81aae8e5889f7e6e79f660465ec58dab2.
Configuration: stacks200/200,BB2,no ante/rake,heroAcAd, explicit two-opponent-hand
support with equal priors, prefix call/open6/3bet18/4bet42, interventions
fold/call/raise90. 50 samples per deal/action=300 total. Fold EV[-18,+18] exact
by chip accounting; other outputs are sample means, not exact equilibrium EV.
First posterior-test fixture mistakenly assigned zero probability to its own
observed open; null posterior correctly caused a test failure. Corrected fixture
now assigns the observed prefix explicitly. No engine validation weakened.

Limits: heads-up explicit support only, not general2..9-player belief inference.
Support completeness remains false; priors are caller supplied. Queried hero
consistency is checked, not every possible unqueried infoset. Statistical
confidence controls sampling error under a fixed deterministic supplied policy;
it does not certify true opponent priors, model correctness or Nash convergence.
Generic native_infoset_ev/hand169_ev stay null. Formal20stacks/sizes, verified
GTO169EV, convergence and Poker ID UI are still unfinished.

Commands:
```
cd /workspace/poker-sns
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_next python3 -B gto/native/test_policy_rollout.py -v
```
Repeat for g12_p1_cache/g12_p1_packed. Native modules are temporary rebuilt
artifacts, not repository dependencies; reconstruct fresh if absent using
`python3 -B gto/native/build_reconstructed.py --work-root /tmp/NEW-FRESH-PATH`.
The pinned source download needs authorized network access. GitHub connector
publication avoids repeatedly requesting shell network access; local/public
commits may have different metadata but must have identical source trees.

Frontend dependency check: `npm ci --offline --ignore-scripts` failed ENOTCACHED
for yoga-layout3.2.1. Prior network npm ci was interrupted at approval. No build,
lint/browser test PASS claimed. No app source changed.

Next:
1. Freeze native average policy and bind sampled belief/action reports to exact
   configuration/history/policy digests before any frontend transport.
2. Extend opponent joint-support handling beyond heads-up with blocker-correct
   multiway posterior and conservation tests; retain full release specification.
3. Validate representative strategy convergence and authentic reach; connect
   verified results to Poker ID's condition search and169 matrix.

No scheduler or independent restart installed. AUTO-RESUME OFF. No production
DB/deploy/main/billing changes. Owner decision only needed to locate missing
formal stack/size fixtures; independent safe implementation can continue.

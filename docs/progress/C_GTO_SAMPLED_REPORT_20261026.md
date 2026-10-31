# Frozen sampled preflop report transport

Published transport HEAD4f26d53a2f93e328bfcf30a5c2390e4d94a4ff89,
treedacdef06886e61928e71527c31031e1dc684f391 (same as local59e5f00).
CI40353864778 SUCCESS: decoded job121680946891 has495 unittest executions
plus25 packed cases=520 PASS, with3native builds/smokes successful.

## Bounded larger-run continuation

The first60000-sample experiment failed closed at the default100000 queried
hero-infoset consistency budget and returned no partial EV. Exposed max_infosets
through belief/action/report APIs, still constrained by existing1..1000000
validator; no consistency check removed. Regression proves limit1 rejects a
two-infoset prefix and explicit limit2 accepts it. Added actual2..9-player,
unequal-stack,0/1BB ante fixed-state EV checks: all-fold payoff is exactly
[-1,+1,0,...,0]. This does not extend explicit beliefs beyond heads-up.

Rollout suite18→20 methods,3variants54→60 PASS (+6). Relative to initial
published9427f6bf:4→20 methods (+16),12→60 executions (+48).

Separate local Next-only larger QA (not CI): explicit max_infosets300000,
same prior/policy/game as earlier300sample example,10000samples per deal/action,
60000total (200x). Runtime60.452s on this executor. Overall simultaneous
confidence95%; hero sample means/chip intervals:
- fold: -18.0000 [-25.0278,-10.9722]
- call: +26.4579 [+19.4301,+33.4857]
- raise-to90 chips: +58.1445 [+51.1167,+65.1723]
Half-width99.3884→7.0278 chips (14.142x narrower), matching sqrt(200) scaling.
These compare interventions against a deliberately supplied check/call opponent
policy and two-hand prior, not an equilibrium response range or GTO action advice.
Fold's true fixed-state value is independently known as-18 despite the generic
conservative sampling interval. No convergence or full opponent support claim.
Evidence: actions-60000.json and benchmark-summary.json under the same QA folder.
Canonical report SHA2565fda3d50ef791f293ecdfb4901e3568dcbea4a5d41b2bff9415c2fbf5467abc5
excludes the trailing file newline. Larger benchmark ran only Next; earlier
300sample comparison across all3variants remains separate evidence.

Input public8916b7e9ed3383cdcbeae778b807a150eb8fe94b / local56c80f1,
same tree02e3ad0b21587e59e8e77e6deeb2120ea97159fd. Exact-head Actions
40353157734 SUCCESS. Existing working changes and earlier commits preserved.

Implemented `preflop_action_report` in policy_rollout.py:
- Requires existing immutable PolicySnapshot; ordinary callbacks refused at this
  transport boundary. Keeps native config, policy and exact input digests.
- Verifies stacks/native rule fields against the advertised configuration.
  Mutated stack or BB ante data with a stale manifest fails before calculation.
- Replays actual preflop history and carries legal decision/stage metadata.
- Dedicated schema `pokerid-sampled-preflop-action-v1` and explicit sample-mean
  estimate kind. Separate from exact169 expectation exports; never routed through
  export_action_classes as if sample means were exact expectations.
- support_complete=false, equilibrium_verified=false, native_infoset_ev=null,
  hand169_ev=null retained. Hash binding is not signature/execution attestation.
- Exposes max_deals up to existing validator limit10000 instead of silently
  pruning to default128. Explicit129-support regression passes without pruning;
  default budget rejects it. Aggregate sampling budget remains independently
  enforced. This does not prove complete opponent support or multiway beliefs.

Validation delta: rollout suite15→18 methods (+3), three-variant45→54
executions (+9), all PASS. Versus initial published9427f6bf rollout4→18 (+14),
12→54 executions (+42). See `docs/qa/preflop-sampled-report-20261026/`.
Regression covers fixed snapshot replay/JSON identity, stale manifest rejection,
and explicit support budget expansion. Existing exact-vs-sampled numerical tests
remain in the same suite; policy/EV methods unchanged by this transport layer.

No TSX/app source changed. App build/lint/browser tests remain NOT RUN after
offline npm ci failed ENOTCACHED. No UI integration or full GTO release claimed.

Current commands:
```
cd /workspace/poker-sns
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_next python3 -B gto/native/test_policy_rollout.py -v
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_p1_cache python3 -B gto/native/test_policy_rollout.py -v
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_p1_packed python3 -B gto/native/test_policy_rollout.py -v
```
For a fresh executor reconstruct pinned native modules as in
`C_GTO_RELEASE_20261026.md`; original G11 recovery is not claimed.

Next concrete implementation: generalize explicit opponent joint support beyond
heads-up with native blocker validation, shared public-observation posterior,
multiway chip/rake conservation, then bind those reports to immutable policies.
Follow with representative native strategy convergence/actual reach and Poker ID
condition search. Exact formal20stack/sizing fixture source is still missing;
preserve full2..9-player/MTT/ring/ante/rake/sizing/169frequencyEV requirements.

AUTO-RESUME OFF, independent automatic restart absent. No production DB, deploy,
main merge, paid service or other development-line PR changes.

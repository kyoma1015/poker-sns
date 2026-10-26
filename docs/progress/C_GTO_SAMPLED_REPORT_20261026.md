# Frozen sampled preflop report transport

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

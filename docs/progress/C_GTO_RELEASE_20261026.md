# GTO preflop release continuation

Scope: PR120 / codex/c-native-hand169-bridge-20261023. Input HEAD
fa5e7553acf50241214a5a975f6b90d951c94bbb. Initial release remains UNFINISHED.

Latest completed publication: 9427f6bf3c57c9f90a64c8c4ca31762489a83360,
same tree8b7c2993f6d3391bc64c3c0c81feda7d2fff1ff6 as local8597439. CI
https://github.com/kyoma1015/poker-sns/actions/runs/40351061844 SUCCESS.
Next continuation: `C_GTO_SAMPLED_BELIEF_20261026.md` records sampled explicit
opponent-belief EV and common-hero four-bet-response action comparisons.

Acceptance criteria chosen before implementation: native legality through four
bets and response, no fabricated unvisited policy, preserved action identity and
frequency sum, explicit EV scope, all existing native variants retained. No
change to SNS/TDA/diagnosis/shared app files or production services.

Implemented:
- `gto.native.preflop`: native public betting-history replay, RFI/limped/open/
  3bet/4bet/5bet+ decision classification, legal fold/call/check/raise-to amounts,
  existing coverage-aware169 frequency export and verified-checkpoint query CLI.
- `NativeGame`: existing native 5%/10% rake with absent/5BB/10BB caps exposed,
  plus no-rake profile (seven distinct configurations). 0/1BB ante and supported
  rates/caps validated before native solver creation. Default contract unchanged.
- Unvisited native average rows fail instead of exporting a fabricated uniform
  policy. Missing/partial reach and EV are not silently completed.
- `policy_rollout`: seeded bounded fixed-policy native chip EV, exact rational
  sample mean, simultaneous Hoeffding seat intervals, chip/rake conservation,
  fail-closed missing/illegal/mutating policies and trajectory budgets. Reuses
  existing chance/strategy validators. Conditional on complete supplied state;
  not an infoset EV estimator or equilibrium proof. Confidence bounds concern
  sampling error only, not belief/model/convergence error.

Observed verification:
- Fresh pinned native reconstruction in `/tmp/pokerid-gto-release-build3`:
  Next/Cache/Packed build+smoke PASS, 320 synthetic poker cases each. This is
  reconstructed pybind11/Abseil, not recovered original G11 environment.
- All existing native test modules plus preflop/rollout tests run separately on
  all three variants. Logs and return codes: `docs/qa/preflop-release-20261026/`.
- Preflop checks cover 2..9 seats, four betting stages, legal responses, short
  all-in not reopening raising, limped-pot classification, five-bet continuation,
  seven rake profiles and BB ante. These are legality/transport tests, not
  strategic optimality tests.
- Rollout means compared with exact native fold and all44 river outcomes,
  including rake/BB ante. Exact and sampled methods share native settlement;
  this does not independently prove settlement correctness for every condition.
- Existing pure Python18, original hand169 acceptance33, Packed25 and Next9 PASS.
- No app source edits. npm ci was interrupted at network approval; app build,
  lint and browser tests NOT RUN. No app QA claim.

Resume:
```
cd /workspace/poker-sns
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_next python3 -B gto/native/test_preflop.py -v
GTO_NATIVE_MODULE_DIR=/tmp/pokerid-gto-release-build3/g12_next python3 -B gto/native/test_policy_rollout.py -v
python3 -B -m gto.native.preflop --module-dir /tmp/pokerid-gto-release-build3/g12_next --stacks 200 200 --history 8 20 44
```
Native history action0=fold,1=call/check, raise ID=raise-to chips+2. Example is
open6,3bet18,4bet42 chips with BB2; output is the response decision. Amounts are
illustrative legal sizes, not the unrecovered authoritative sizing fixtures.
For trained frequencies add --checkpoint and --reach-weights together; weights
must cover exactly the selected native infosets. Caller supplied weights are
not authenticated reach provenance. Never publish these outputs as solved GTO.

Next priority:
1. Establish authenticated general preflop reach and opponent support; integrate
   frozen native policy EV evaluation with belief aggregation without inventing
   missing policy or truncating postflop continuation to a showdown.
2. Recover authoritative20 stacks/sizes and G1..G9 original expected fixtures;
   existing source tree describes them as missing. O06 candidate stacks are not
   a substitute for full formal specification. User asked asynchronously for
   source location; development need not wait for unrelated work.
3. Genuine convergence/exploitability assessment for the target game, then
   production-quality Poker ID range search with provenance, coverage, verified
   EV and convergence status. UI connection remains UNFINISHED.

No permanent worker/scheduler/automatic restart configured. AUTO-RESUME OFF.
No main merge, production DB/deployment or paid service operations performed.

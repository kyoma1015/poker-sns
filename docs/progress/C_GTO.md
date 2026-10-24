# C | GTO handoff closure and remaining gates
Date: 2026-10-20 JST
Source: chore/codex-handoff-artifacts-20261020 @ 8509484bf9186534ca10694eb62aba7075395aee.
Status: latest active milestone below supersedes the initial handoff-only state: reconstructed native build PASS; original G11 parity/historical resume BLOCKED.

## Received actual sources, durable location and re-access
All transferred bytes are preserved under handoff/gto/ on this integration branch. Clone/fetch this branch, then run the commands below. The handoff branch remains unchanged. Original seven ZIPs and vendored ZIP are NOT proved received by a hash ledger.
Compressed payloads use strict Base64 plus zlib; native sources are restored only in memory or a temporary directory. Do not overwrite original artifacts.

| Restored source | Bytes | SHA-256 |
|---|---:|---|
| g12_next_solver_disk.cc | 31431 | 57a03f3cc6fafb0bbf5d1f333b18188b35720a69693519b5e955a8656507c09a |
| g12_p1_cache_solver_disk.cc | 34044 | 3ae79dfef498306b87bfc536be919d8a54b58313b8f9647b86793d7840e1d90a |
| g12_p1_packed_solver_disk.cc | 32084 | f3b31a0703d130372e84b53ee7b05ab37b7a40fcf3856f6be5b45b7dfedfdb0b |
| g11_rules_embed.h | 10159 | 870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353 |
| pokerid_rules.py | 10318 | 456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a |
| g12_p1_packed_live_backend.py | 7749 | 9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52 |
| build_original/g12_p1_cache/build.sh | 781 | e4d6b89c4ef5bb2509dca2f9d4231c1e8ed26b9476a40e5a9edd71af74687235 |

`python handoff/gto/verify_native_solvers.py`: 3 variants PASS.
`python handoff/gto/tests/run_backend_tests.py`: header/rules/backend hashes PASS; SQLite 25 PASS (11 normal, 9 invalid, 5 transaction checks). Evidence: docs/qa/integration-20261020/gto.log.
The backend has no internal rollback guarantee: after a malformed 257th row, 256 partial writes can remain in the active transaction, invisible to another connection. Caller rollback removes them and preserves prior committed rows/metadata. writes counter is not a committed-row count. No historical checkpoint was opened.

Next backend uses ordinary commit; Packed/Cache require commit_packed. Next / Packed / Cache remain distinct; no canonical implementation selected. Hash verification and Python tests do not prove native ABI compatibility, numerical accuracy or G11 parity.

## Native-build dependencies still missing
The latest source-branch Git tree contains no ZIP and no patched/ vendor closure. The 1,588-file SOURCE_SHA256.csv/vendor bundle has not been independently received or verified here.
Required original nested ZIP locations (reported in the source discovery document; actual ZIP bytes unavailable):
- assets/PokerID_OpenSpiel_G11修正版(1).zip -> PokerID_OpenSpiel_G11/patched/pybind11/include/pybind11/ (entire transitive header closure)
- same nested ZIP -> PokerID_OpenSpiel_G11/patched/open_spiel/abseil-cpp/absl/ (headers and random/discrete_distribution.cc with transitive closure)
- source Packed backend originally assets/g12_p1_packed/g12_p1_live_backend.py; cache copy byte-identical according to sender report, now transferred backend bytes independently verified above.
Exact pybind11/Abseil versions and source provenance: UNKNOWN until vendor bytes/manifest accessible. Do not substitute latest packages and call it the original environment.
Build options from preserved build.sh: -O2 -std=c++20 -fno-fast-math -ffp-contract=off -fPIC -shared, Python include/EXT_SUFFIX, matching Python ABI, CXX; Darwin adds -undefined dynamic_lookup. All variants require matching headers, g11_native_state.h and g12_numeric.h. Original official build.sh directly covers Cache; reusing it for Next/Packed needs explicit variant/module validation.
Do not build until dependency closure is present. No dependency installation/native build performed in this integration task.

## Historical calculation gates
G11 baseline expected outputs, original run settings/seeds, parity logs and matching complete checkpoint (including metadata/RNG) remain unavailable/UNKNOWN. No assertion of G12 resume readiness.
Safe now: source comparison, strict hash checks, temporary SQLite Python tests. After vendor receipt: isolated separate native builds/import/numeric-environment tests. Only after baseline/checkpoint validation: G11 parity and historical resume tests on copies.
These C-lane blockers do not prevent A/B/D/SNS branch development.

Existing Next backend unit suite: `python -B handoff/gto/g12_next/g12_p1_live_backend_tests.py` — 9 PASS using temporary SQLite only (docs/qa/integration-20261020/gto-next.log). Added to CI. Packed25 + Next9 = 34 Python backend tests; this is not native solver/G11-parity coverage.

## Active milestone update — 2026-10-20
Base PR13: 3ca87764e988cac588fef915d48823702a1a3326. Work branch: codex/c-gto-active-milestones-20261020.
New policy source handoff ae22acd1ba5d167f1d7111069966dda672260129: GTO_ACTIVE_CONTINUOUS_DEVELOPMENT_20261020.md. The old no-build statement above described missing *original* dependency closure during handoff; owner now permits pinned isolated reconstruction. Original source/dependency/checkpoint provenance is not retroactively marked recovered.

Milestone 1 completed: pinned pybind11 2.13.6 wheel and Abseil 20240116.2 source (SHA-256 checked), reproducible isolated build tool, separate Next/Cache/Packed copied sources/directories/import processes. All 3 unmodified C++ sources build with original -O2/-std=c++20/-fno-fast-math/-ffp-contract=off/-fPIC/-shared options. Python 3.12.14 cpython-312-x86_64-linux-gnu; Debian GCC 14.2.0; long_double_digits=64. This is a reconstructed environment, NOT original G11 vendor/ABI restoration. See gto/README.md and docs/qa/gto-active-20261020/native-manifest.json.
Each variant passes extended-reach cancellation (0.5^1100), invalid operand/legacy-mode rejection, finite normalized toy policies, 200 synthetic matching-pennies iterations, temporary SQLite reopen/resume and memory/disk checkpoint byte equality. All three produce the same synthetic checkpoint SHA b38355859e67d65e2b50fdf057153c0e1ba6237cdab6d8355617298878d685db on this environment. This is not G11 parity or an optimal strategy proof.
Additional bounded native-poker smoke: each variant passes 320 one-iteration cases across 2–9 players, 20 synthetic equal-stack values 2..40BB, cash rake 1/10 + BB ante and MTT chipEV/no-rake + BB ante. Total 960. Owner's exact 20 stack conditions/bet-size fixtures and expected settlement results remain UNKNOWN; this synthetic coverage does not replace them.

Milestone 2 completed: checkpoint integrity boundary and 169-class export validation.
Actual issue reproduced: preserved native load_binary accepts a modified checksum trailer. Original C++ source is retained; new load_verified_checkpoint streams to a private temporary snapshot, verifies SHA/magic/contract/bounded header, then delegates full row/mode validation. New consumers must use this wrapper. Raw save_binary emits a checksum-free payload; no historical format migration is inferred.
Hand169 component validates all 1326 distinct combinations, 13 pairs/78 suited/78 offsuit classes, reach-weighted strategy/EV, missing coverage, duplicate/invalid cards/probabilities/weights, and explicit unknown/zero-reach output. It produces no solver frequencies/EV itself.
`python -B -m unittest discover -s gto/tests -v`: 18 PASS (checkpoint 8 + hand169 10).
Existing backend regressions 34 PASS; app regressions 89 PASS; npm ci/build/lint PASS with existing warnings. Browser/UI source was unchanged. Evidence and exact run commands under docs/qa/gto-active-20261020/ and gto/README.md. Dedicated PR CI runs the native reconstruction; it is a finite verifier, not a permanent worker.

Remaining: genuine vendor 1,588-file bundle, G11 expected data/settings, exact target stack/bet configurations, historical checkpoint and ABI checks, settlement/parity/convergence/representative benchmarks. No original ZIP bytes/checkpoint appeared in current handoff Git tree. No canonical solver selected, no old checkpoint opened, no production/main/DB operations. Next tasks: expected-value settlement fixtures, checkpoint format/compatibility inventory on copies, and connecting verified 169 export to actual native row output without inventing EV.

## Native batch lifecycle — 2026-10-23
New finite native training/verified checkpoint continuation is described in
`docs/workers/GTO_NATIVE_TRAINING_BATCH_20261023.md`. This is a PR20 follow-up,
not a replay of existing settlement/hand169 patches or recovered G9 baseline.
Local native tests: eight per separate Next/Cache/Packed process, plus existing
18 Python tests. Original G9 source, 20 owner stacks, G11 ABI and full poker
convergence remain unproved; native exported EV remains null. No retained state,
controller, scheduler or production changes.

## Native hand169 wiring and finite real-poker oracle — 2026-10-23
PR115 follow-up adds actual native infoset-context → 169 frequency export with
mandatory caller mass and null EV. Exact native poker policy oracles cover fold,
known river and all44 river chance outcomes. It reuses the exact PR103 hand169
blob and33 original acceptance tests; these are not newly implemented fixes.
See docs/workers/GTO_NATIVE_HAND169_BRIDGE_20261023.md. Complete coverage, authentic
reach mass, original G9/G11 and full poker convergence remain unproved.

## Initial chance marginal — resumed 2026-10-24
Preserved interruption input cca4c0e and uncommitted module resumed. New source
proves initial uniform-card own ordered-hand probability1/2652 for2..9 players,
only exact first preflop actor/no history/fixture/prefix, with native/context hash
evidence. Next/Cache/Packed10cases each pass with complete verified local modules;
checkpoint/RNG/policy equality and1326/169 coverage included. Wrong incomplete
local artifact path failure is retained, not a source fix. See
GTO_INITIAL_CHANCE_REACH_20261024.md. General action reach, native EV, G9/G11 and
poker convergence remain unproved; no state/controller/scheduler adoption.

## Finite history reach / conditional EV — 2026-10-24
Saved initial-chance branch retained. New history_reach.py separates exact chance
mass and per-player explicit strategy mass on finite NativeState paths, then
connects the existing oracle to conditional complete-state chip EV and branch
contribution. Learned-row adapter refuses missing/unvisited policy; infoset EV
remains null. Local232PASS (old187+45 across3variants), no PR/CI started.
See GTO_HISTORY_REACH_EV_20261024.md. General belief/infoset reach, justified169EV,
originalG9/G11 and full poker convergence remain gates. No specification shrink.

## Bounded conditional belief / immutable learned policy — 2026-10-24
Existing branch continues from e8e40bf. Exact finite heads-up explicit support
prior→public chance/per-player strategy→posterior→conditional EV now available;
immutable copied native rows survive later training. Local271PASS (old232+39),
3separate variants, no new PR/CI. See GTO_BOUNDED_BELIEF_20261024.md. Conditional
full-state policy is NOT information-set strategy proof; native169EV remainsnull.
No originalG9/G11/history compatibility or convergence success claimed.

## Public observation conditioning / queried hero consistency — 2026-10-24
Cycle2 adds explicit blocker-conditioned support with exact compatible/removed
prior mass, native history/advertised-board equality and queried hero-infoset
policy consistency. Local310PASS (old271+39),3variant exact canonical output match;
see GTO_BELIEF_OBSERVATION_20261024.md. Null remains for native169EV and impossible
observation, no equilibrium or originalG9/G11 claim. No PR/CI/production adoption.

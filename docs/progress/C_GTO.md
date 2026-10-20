# C | GTO handoff closure and remaining gates
Date: 2026-10-20 JST
Source: chore/codex-handoff-artifacts-20261020 @ 8509484bf9186534ca10694eb62aba7075395aee.
Status: CONDITIONAL PASS for Python/source inspection; native build and historical resume BLOCKED.

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

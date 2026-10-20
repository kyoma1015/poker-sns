# GTO isolated native build evidence — 2026-10-20

**Scope:** Sender-side isolated local container, **NOT Codex**. No GitHub binary dependency transfer has occurred. Do not mark GTO-HANDOFF-11 as unblocked in Codex.

## Verified results

Original source ZIP: `PokerID_GTO_G12_NATIVE_SOURCE_TRANSFER_20261020.zip`. Original GTO archive supplied each variant's `g11_native_state.h`. Vendored dependency ZIP: `PokerID_GTO_G11_VENDORED_DEPENDENCIES_20261020.zip` (1,590 entries). Extracted into separate isolated work directory.

Each source variant compiled as an independent Python extension using `c++ -O2 -std=c++20 -fno-fast-math -ffp-contract=off -fPIC -shared`, its own `g12_solver_disk.cc`, vendored `patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.cc`, and the vendored include paths from the original build script. **All three compiler invocations returned exit code 0**. Visibility attribute warnings occurred but did not fail compilation.

| Variant | Compile | Separate-process Python import |
|---|---|---|
| G12 Next | PASS (exit 0) | PASS (exit 0) |
| G12 P1 Packed | PASS (exit 0) | PASS (exit 0) |
| G12 P1 Cache | PASS (exit 0) | PASS (exit 0) |

All three imported modules expose `NativeState`, `Solver`, `test_stable_importance_ratio`, and `validate_probability_product`. The environment used Python **3.13**, so this is **not** a reproduction of Codex's Python 3.12.14 ABI. All modules were built separately to avoid `pokerid_g12` module-name collisions.

## Not proven

- The vendored ZIP is **still unavailable to Codex** and has **not** been committed to GitHub.
- No native solver instantiation, numeric edge-case test, packed C++ to Python SQLite integration, learning, performance comparison, or checkpoint replay was run.
- The original environment's exact Python/compiler versions were not reproduced.
- No solver variant has been selected as canonical.
- No main merge, production deploy, Supabase mutation, or historical checkpoint change.

## Next

Find a verifiable transport route for the vendor ZIP or dependency closure into Codex. Then independently repeat the builds in Codex's Python 3.12 environment. Do not confuse successful sender-side build/import with Codex availability or functional correctness.

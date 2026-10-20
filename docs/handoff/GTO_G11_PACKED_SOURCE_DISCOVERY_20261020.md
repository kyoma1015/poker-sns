# GTO-HANDOFF-07 follow-up: source ZIP independently inspected (2026-10-20)

The sender **opened and read** the original `/mnt/data/PokerID_Codex_GTO_HANDOFF_PACKAGE_20261020.zip` and reduced `PokerID_GTO_G12_NATIVE_SOURCE_TRANSFER_20261020.zip`. This is a new primary-source finding, not an inference from a previous ledger.

## Critical discovery: commit_packed backend exists

Both of these original ZIP members **define `def commit_packed(self, payload, rng, iteration, visits)`**:

| Original ZIP member | Bytes | SHA-256 |
|---|---:|---|
| `assets/g12_p1_cache/g12_p1_live_backend.py` | 7749 | `9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52` |
| `assets/g12_p1_packed/g12_p1_live_backend.py` | 7749 | `9d166dfbd0d9da199585de631788e03636c295f595d568451239f0c0e652da52` |

These two copies are byte-identical. The previously transferred `handoff/gto/g12_next/g12_p1_live_backend.py` is an older/different variant without `commit_packed`. **Do not treat the missing API in Next as proof that the packed backend was never implemented.**

The packed version is **not yet transferred to GitHub**. It exists in the original sender ZIP and needs exact-byte migration plus independent Codex verification.

## Official original build scripts

`assets/g12_p1_cache/build.sh` and `assets/g12_p1_packed/build.sh` are byte-identical, 781 bytes, SHA-256 `e4d6b89c4ef5bb2509dca2f9d4231c1e8ed26b9476a40e5a9edd71af74687235`. The cache script was copied to `handoff/gto/build_original/g12_p1_cache/build.sh`; Codex must independently compare its SHA-256 before treating the transfer as verified.

The scripts use `-O2 -std=c++20 -fno-fast-math -ffp-contract=off -fPIC -shared`, compile `g12_solver_disk.cc` plus `patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.cc`, and include vendored `patched/pybind11/include`, `patched`, `patched/open_spiel/abseil-cpp`, and Python include directory. On Darwin they add `-undefined dynamic_lookup`. Output extension is Python `EXT_SUFFIX`.

## Original G11 nested archive

Original ZIP member `assets/PokerID_OpenSpiel_G11修正版(1).zip` was read directly:

- Byte size **204756925**; SHA-256 `2ba54faad3367480a08bb91a02620f620b64ff95b8e29c36a2351c35cecbb4f5`
- **8724 entries** (count includes directories)
- `PokerID_OpenSpiel_G11/patched/pybind11/include/pybind11/pybind11.h` exists
- `PokerID_OpenSpiel_G11/patched/open_spiel/abseil-cpp/absl/random/discrete_distribution.h` exists

These are **confirmed paths inside the nested ZIP**, not files currently present in GitHub. Avoid committing the entire ~205MB nested archive; select only dependency closure or use a separate large-file transfer mechanism.

## Reduced ZIP inventory

The reduced ZIP has 23 original source files, plus `SOURCE_SHA256.csv` and `README.md`. It includes the packed and cache Python backends, so there is no need to transfer the entire original ZIP to retrieve the packed backend.

## Next

1. Verify the transferred original build script SHA-256.
2. Transfer `assets/g12_p1_packed/g12_p1_live_backend.py` exactly; verify its 7749-byte SHA-256.
3. Inventory minimum pybind11 and Abseil transitive dependencies from the nested archive.
4. Only after dependency closure is present, attempt isolated C++ build. Keep source variants and build outputs separated.
5. Do not modify main, production, Supabase, or old checkpoint state.

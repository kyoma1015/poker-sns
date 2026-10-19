# GTO native solver transfer wave 3 — 2026-10-20

**Current status: three C++ solver files are physically stored on GitHub as compressed Base64 and successfully fetched through the GitHub connector. Codex independent source-byte verification is PENDING.**

Branch: `chore/codex-handoff-artifacts-20261020`

| Original variant | Compressed payload in `handoff/gto/compressed/` | Original size | Original SHA-256 | GitHub blob SHA of encoded file |
|---|---|---:|---|---|
| G12 Next | `g12_next_solver_disk.cc.zlib.b64` | 31,431 | `57a03f3cc6fafb0bbf5d1f333b18188b35720a69693519b5e955a8656507c09a` | `6618b86326200e07a9ae3c710fe865bed7e043e8` |
| G12 P1 Cache | `g12_p1_cache_solver_disk.cc.zlib.b64` | 34,044 | `3ae79dfef498306b87bfc536be919d8a54b58313b8f9647b86793d7840e1d90a` | `94d9f5f0061e7722ef5e9cd12fb25039da5464d0` |
| G12 P1 Packed | `g12_p1_packed_solver_disk.cc.zlib.b64` | 32,084 | `f3b31a0703d130372e84b53ee7b05ab37b7a40fcf3856f6be5b45b7dfedfdb0b` | `96a36d80cedac851c3ded3cb9cba4980398850b0` |

All source bytes came from the small native-source ZIP extracted from the original GTO package. Variants are **NOT interchangeable and are not yet ranked by recency or correctness**.

## Receiver test — no ZIP attachment required

At branch HEAD run:
```sh
python handoff/gto/verify_native_solvers.py
```
It reads the three `.zlib.b64` files, strict Base64-decodes, zlib-decompresses in memory, and checks sizes and original SHA-256. It does not write anything, connect to DB, or run a solver.

After verification, optionally extract to an isolated scratch directory before dependency audit. Also cross-check `g11_native_state.h`, `g11_rules_embed.h.zlib.b64`, `g12_numeric.h` and `pokerid_rules.py.zlib.b64` from this branch.

## Still blocked

- Complete G11 baseline and build environment (OpenSpiel Abseil headers, pybind11 etc), C++ compilation and comparison.
- Big SQLite files / G11 checkpoints and exact continuation.
- 9500 iterations independent reproduction and full 7-ZIP handoff.

This is **not** authorization to merge `main`, deploy, run production SQL or modify Supabase. Older documentation stating native solver files are not uploaded was written before wave 3; prefer this document and actual GitHub tree for this branch.

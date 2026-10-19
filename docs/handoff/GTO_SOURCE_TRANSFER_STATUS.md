# GTO source handoff — transfer evidence 2026-10-20

Status: **PARTIAL**. Do not claim G12 solver reproducibility or checkpoint continuity yet.

Source ZIP: `PokerID_Codex_GTO_HANDOFF_PACKAGE_20261020.zip`
Sender ZIP measured SHA-256: `88a3f6683f28340d662fd26a1ed541531ae2f84a0c341177c6ca2ce4d520e713`
Source archive member prefix: `assets/g12_next/`.

## Transferred without modifications

| GitHub file (under `handoff/gto/g12_next/`) | ZIP member name | Raw SHA-256 | Git blob SHA verified after fetch |
|---|---|---|---|
| `g12_p1_live_backend.py` | `assets/g12_next/g12_p1_live_backend.py` | `6178fe9f04635fcbb572ebdf5f13dce6e0289f69a686c5967951363e328ee3b6` | `4de827c5464923e7a6e8fa942aad65ac5875f5f1` |
| `g12_p1_live_backend_tests.py` | `assets/g12_next/g12_p1_live_backend_tests.py` | `24acc6e25366ea76bd42bdadc0e52e0aadea6f88cbe72358e59c77c50daaf256` | `c1f3bf93e9d9dffd56feabae2e465be7ac04ac58` |
| `g12_numeric.h` | `assets/g12_next/g12_numeric.h` | `0a4bfce61ebbb8ddedbeaebb7ecd9131f5c62326dc03463d04487742a975e578` | `44b3d71fc56f4c135da73b16b7c26924a51b4a83` |

### Test on sender runtime

Extracted the two Python files from the original ZIP into a temporary directory and ran:
`python -m unittest -v g12_p1_live_backend_tests`

Result: **9 tests passed** (0 failures). No DB outside a temporary directory was modified.

## Missing and BLOCKED

- C++ solver source `assets/g12_next/g12_solver_disk.cc` and its dependency headers.
- Large nested archive `assets/PokerID_OpenSpiel_G11修正版(1).zip` (204,756,925 bytes uncompressed as outer member).
- Solver tests, benchmarks, complete build integration and verification of source revision.
- Binary data `assets/g12_endurance/disk9501.bin` and SQLite state `assets/g12_endurance/endurance.sqlite`, additional absent checkpoint artifacts.
- Reproduction of 9500-iteration result, G11/G12 complete build and G12 restart.

All above remain **not transferred and unverified by Codex**.

## Boundary

This directory is preservation staging, **NOT** runtime production code or a completed solver implementation. No `main` merge, production Supabase writes, deploy, paid storage, or new solver features without explicit owner permission.

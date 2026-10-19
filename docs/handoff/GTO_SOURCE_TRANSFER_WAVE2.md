# GTO source handoff wave 2 — 2026-10-20

Branch: `chore/codex-handoff-artifacts-20261020`
All copied members were taken from the original GTO ZIP, then GitHub fetched and checked against local Git blob SHA-1. These are **historical handoff artifacts**, not yet a compilable complete solver.

## Newly transferred exact original files

| File in `handoff/gto/g12_next/` | Local ZIP member bytes | Expected and fetched Git blob SHA |
|---|---:|---|
| `g12_full52_native_smoke.py` | 1608 | `091c4f1c9dd2c0aea28a2649d007559d0fe27a5a` |
| `verify_resume.py` | 2183 | `2e06f2587c64eb0cfa404ff68daef9885c09f656` |
| `g11_native_state.h` | 3913 | `45109e06d1840c5ee10d226bc72a51b10eebbd65` |

The smoke and resume scripts are evidence of prior experiments, and are NOT standalone: imported native G11/G12 modules, rules module, SQLite state and checkpoint fixtures have not been transferred.

## Solver core located in source ZIP, still NOT transferred

| Source member | Bytes | Raw SHA-256 |
|---|---:|---|
| `assets/g12_next/g12_solver_disk.cc` | 31431 | `57a03f3cc6fafb0bbf5d1f333b18188b35720a69693519b5e955a8656507c09a` |
| `assets/g12_p1_cache/g12_solver_disk.cc` | 34044 | `3ae79dfef498306b87bfc536be919d8a54b58313b8f9647b86793d7840e1d90a` |
| `assets/g12_p1_packed/g12_solver_disk.cc` | 32084 | `f3b31a0703d130372e84b53ee7b05ab37b7a40fcf3856f6be5b45b7dfedfdb0b` |
| `assets/g12_next/g11_rules_embed.h` | 10159 | `870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353` |
| `assets/g12_next/pokerid_rules.py` | 10318 | `456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a` |

These three native solver variants differ and must **not be silently merged or described as one latest variant**. Decide canonical version only after reviewing dated benchmark evidence and the G11 dependency set.

## Status and gate
- Exact source migration: **PARTIAL**; six source/script files total across waves 1 and 2.
- Native compile, native smoke test, true 9500-iteration restart: **BLOCKED** by dependency and runtime-data gaps.
- No changes to `main`, production app, Supabase, deployment, or original ZIP.

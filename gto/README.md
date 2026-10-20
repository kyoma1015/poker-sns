# GTO active development

These modules advance prerequisite milestones without reducing the final target:
2–9 players, 20 specified stack conditions, ring rake, BB ante, MTT chipEV,
specified bet sizes, and 169-hand frequency/EV. The exact owner/G11 20-stack
fixture set has not been recovered; synthetic smoke coverage is not its substitute.

## Reconstructed native environment

Requires Python 3.12+, a C++20 compiler with extended-range `long double`, and
network access for two pinned public archives. No pip install, CMake, credentials,
DB service or original ZIP is required by the script. Original transferred sources
and all historical checkpoints remain untouched.

```sh
python handoff/gto/verify_native_solvers.py
python -B -m unittest discover -s gto/tests -v
python -B gto/native/build_reconstructed.py --work-root /tmp/pokerid-gto-fresh-build
```

Use a **fresh** scratch path outside the repository. Existing paths are refused.
Archives have fixed versions and SHA-256 pins in `build_reconstructed.py`.
Every variant gets a separate source/module directory and subprocess import.
`manifest.json`, `build.log`, `smoke.log` are written only under that scratch path.
This is pybind11 2.13.6 + Abseil 20240116.2 reconstruction, **not** the original
G11 vendor bundle or original ABI validation. It does not establish numerical
parity with G11 or reproducibility of historical performance.

Native smoke includes finite/normalized policies, extended-reach cancellation,
invalid-operand rejection, 200-iteration synthetic matching-pennies work,
temporary SQLite reopen/resume, RNG/state parity and checkpoint byte equality.
It additionally runs one iteration for 2–9 players × 20 **synthetic equal-stack**
values (2,4,...,40BB) × cash-rake/BB-ante and MTT-chipEV/BB-ante configurations:
320 small native-poker cases per variant. This proves bounded execution, not
convergence, chip/rake correctness, owner stack-fixture parity or feature completion.
No existing checkpoint is used.

## Checkpoint integrity boundary

The preserved C++ `load_binary` reads a 32-byte trailer without verifying SHA-256.
This was reproduced by changing only the trailer of a new synthetic checkpoint:
raw native import accepted it. **Do not call it directly on unverified files.**
Use `gto.native.checkpoints.load_verified_checkpoint` in new code. It streams to a
private temporary copy, checks digest, magic, contract and bounded header fields,
and passes only that immutable snapshot to native structural/mode validation.
The original is opened for reading only. SHA-256 is corruption detection, not
sender authentication. `save_binary` creates a payload without the digest trailer;
the test harness appends a digest only to its newly created synthetic copy.
Historical raw/checksummed format ambiguity must be resolved before any resume.

## 169-hand export component

`gto.hand169` enumerates the standard 52-card deck and all 169 classes, and validates
1,326 concrete combinations before reach-weighted frequency/EV aggregation.
Incomplete coverage is rejected by default; explicit partial mode labels coverage.
Duplicate combinations, NaN/Inf/negative mass, invalid policies/cards and overlong
policies fail. Zero-reach classes and unknown EV remain `None` rather than invented
zero values. This component consumes solver output; it does **not** generate an
optimal strategy or claim any EV results.

## Remaining milestones

1. Recover genuine G11 vendor manifest, original 20-stack specifications, baseline
outputs/settings and complete checkpoint; independently verify bytes/provenance.
2. Pin original dependency/ABI environment and compare it to the reconstructed one.
3. Native settlement/rake/ante fixtures with expected results, deterministic
G11/G12 parity, convergence/exploitability and representative performance runs.
4. Checkpoint contract/integrity migration on **copies**, after formats are known.
5. Connect 169-class aggregation to verified native policy/EV export and all target
configurations. Keep Next/Cache/Packed distinct; no canonical variant selected.

CI verifies this bounded reconstruction on relevant PRs. It does not start a
permanent development worker, resume old calculations or release production.

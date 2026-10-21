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

## Hand-derived settlement milestone (Issue22)

`gto/fixtures/settlement-v1.json` contains 17 **synthetic, hand-derived** expected
settlements. They are candidate-rule examples, not recovered G11 baseline data or
newly approved house rules. The suite compares each implementation to those
explicit expectations and then compares the full Python/native result, legal
moves and state after every action/street.

```sh
python -B -m unittest discover -s gto/tests -v
python -B gto/native/settlement.py
# After a fresh reconstructed native build (one invocation per scratch root):
python -B gto/native/settlement.py --native-root /tmp/pokerid-gto-fresh-build
```

The final command compiles a **test-only** bridge exposing the unchanged embedded
Ledger header already used by all G12 variants; no solver module/API is replaced.
It checks the original header hash before compiling and uses the pinned pybind11
headers from the reconstructed build root. Only a new `settlement-probe/` directory
is written. Existing output directories are refused.

Coverage includes ante/blind priority, short BB ante, after-ante stack basis,
no-flop-no-drop, uncalled refunds, multiple side pots, folded-seat ineligibility,
odd-chip seat ordering, rake with/without dead ante, whole-hand/per-pot caps and
floor/nearest/ceil rounding. The simple integer hand-strength vectors deliberately
isolate settlement from card evaluation; they are not poker hands or solver EVs.

Unresolved candidate-rule edge: a BB whose entire short stack becomes dead ante,
followed by refund of the unmatched SB, leaves no `positive_live` eligible seat.
Both preserved kernels reject this state. `all_live` is covered separately; no rule
profile was silently changed. See docs/qa/gto-settlement-20261020/limitations.json.
The next independent worker task is gto/tasks/rank7-next.json (hand-derived card
ranking/category/tiebreak fixtures). Historical baseline/checkpoint gates remain.

## Synthetic rank7 milestone (Issue22 continuation)

`gto/fixtures/rank7-v1.json` pins 16 hand-derived seven-card expected rank tuples:
all nine categories, ace-low straight/straight flush, two trips choosing the
higher full house, board-playing ties and pair kickers. It contains synthetic
card examples, not recovered G11 baselines or solver strategy output.
`run_rank7_case` validates seven distinct integer cards in 0..51 before invoking
either preserved kernel, including rejecting booleans/nonintegral values. This
boundary matters because the preserved Python rank7 checks uniqueness/count but
omits deck bounds. Original transferred Python/C++ bytes remain unchanged.

The existing native settlement command now additionally compiles/uses the exact
header's rank7 and compares both kernels to explicit expected tuples. It also
retains all 17 settlement cases. Run Python fixtures with
`python -B -m unittest discover -s gto/tests -v`; the protected worker acceptance
is `python -B -m unittest discover -s tests/worker_acceptance -v`.
Native parity uses the documented fresh scratch-root build and settlement command.
Card evaluation parity does not establish strategy optimality, convergence,
original G11 compatibility, or historical checkpoint resumability.

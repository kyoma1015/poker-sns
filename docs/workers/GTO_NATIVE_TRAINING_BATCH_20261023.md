# GTO native finite training continuation — 2026-10-23

## Scope and immutable baseline
This is a new, manually invoked training lifecycle on exact PR20 base
8faea88802d0d34ae3e0319399e7f55ba71a9fcd. It does not transplant or replace
PR75/103/108/110 numerical/settlement changes. Only new training modules, tests,
CI and documentation are changed. Preserved compressed C++ sources, original
rules/header bytes, historical checkpoints and retained Issue22 SQLite are untouched.

Input commit 8e01bd4 pins the eight acceptance methods. Before implementation,
import failed with ModuleNotFoundError (one import ERROR; **zero executed test
methods**, not eight witnessed assertion failures). This is an absent lifecycle
feature, not a claim that eight native computations failed. The unchanged tests
then execute against actual native extensions for each variant.

## Actual engine advancement
`gto.native.training` adds finite real Solver.run_iteration training batches,
explicit 2–9 player native poker configuration, checksummed immutable checkpoint
publication, verified resume, and native average-policy export. A split 3+3 native
training run must equal uninterrupted 6 iterations in RNG, every row and complete
checkpoint bytes. Stop is cooperative **between native iterations**; an individual
iteration is not preempted by this module. Native iteration failures propagate;
poisoned partial iterations are never checkpointed by a catch-and-save path.

Checkpoints use same-filesystem fresh temporary files, streaming SHA-256 trailer,
fsync, preflight validation and exclusive hard-link publication. Existing paths,
including resume inputs, are never overwritten. Filesystems without hard-link
support fail closed. Atomic visibility does not promise power-loss durability of
the containing directory. This adds no scheduler, lease or autonomous worker.

Example (fresh output directory, never a historical checkpoint):

    python -B -m gto.native.training --module-dir /tmp/reconstructed/g12_next --stacks 4 4 --bb 2 --bba 2 --seed 17 --iterations 100 --checkpoint /tmp/new-run-001.bin --export /tmp/new-policy-001.jsonl

A later batch uses `--resume /tmp/new-run-001.bin` with another fresh destination.
The configuration contract hashes stacks and explicit candidate rule settings;
original G11 ABI/schema equivalence is not implied. Native epsilon/alpha/modes
remain validated by the native loader. Next, Cache and Packed are tested in
separate processes; no canonical winner or cross-variant ABI compatibility is selected.

## Measurements and limitations
Eight native tests per variant cover 2–9 players, 3+3 exact continuation,
corrupt digest refusal, mismatched stacks/rules, existing-file protection,
publication failure cleanup, completed-iteration stop/resume and finite bounds.
Local evidence and actual native 2/6/9-player 100-iteration throughput are in
`docs/qa/native-training-batch-20261023/`.

Exact matching-pennies NashConv is computed from actual trained native policies:
|2p−1|+|2q−1|. This is a two-action hidden-move zero-sum toy metric only; its
observed values are not poker convergence/exploitability proof. Average-policy
export retains native `ev: null`: no fabricated EV estimates are introduced.

## Final-spec status (individual assessment)
| Requirement | Status | Evidence / remaining gate |
|---|---|---|
| 2–9 players | PARTIAL | Native batch tests execute every count; full strategy validation absent |
| 20 owner stack configurations | BLOCKED | Exact owner/G11 fixture set not recovered; synthetic equal stacks are not a substitute |
| Cash rake | PARTIAL | Candidate native rules/rake path exists; full cash strategy QA absent |
| BB ante | PARTIAL | Explicit setting and actual native training verified; all profiles not proved |
| MTT chipEV | PARTIAL | Zero-rake native training; tournament strategy accuracy unproved |
| All specified bet sizes | PARTIAL | Existing native legal actions preserved without pruning; authoritative target size specification not recovered |
| 169-hand action frequencies | PARTIAL | Existing PR20/103 aggregation is separate; live native export mapping still unconnected |
| 169-hand EV | PARTIAL | Aggregator accepts EV; native outcome-MCCFR table does not estimate it |
| Side pot / all-in / settlement | PARTIAL | Existing PR75/103 hand-derived regression; end-to-end strategic validation absent |
| Numerical stability / reproducibility | PARTIAL | Seed/RNG/row/checkpoint equality for new native batches; broad numerical/strategy proof absent |
| G1–G8 original milestone completion | BLOCKED | Original per-stage source/acceptance evidence not recovered |
| G9 original nine-player baseline transplant | BLOCKED | Original baseline source/provenance and acceptance absent; this new lifecycle is not called G9 completion |
| G11 ABI / old checkpoints | BLOCKED | Genuine original vendor/ABI, baseline and complete matching checkpoint still absent |
| Full poker convergence | BLOCKED | Toy metric and bounded training do not establish full poker exploitability |

Next: recover G9 original source/acceptance; add exact small real-poker reference
strategy evaluation; connect exported infoset policies to verified 169-hand
mapping and separately justified EV estimates. No main merge, controller adoption,
production operation, paid service or independent launch is part of this PR.

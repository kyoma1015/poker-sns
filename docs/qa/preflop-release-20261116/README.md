# Release delivery evidence, not a GTO promotion

Formal score0/12→0/12. See acceptance-map.json for each requirement, actual
implementation, minimum remaining work and blocker. Old checklists are unchanged.

## Original conditions

The reachable history contains248commits. The original roadmap introduced at
 d03148b835efb8960e8fd443b78ae981c3ebbd8d has O06(line241): MTT
10/15/20/25/30/40BB and cash100BB as **candidates**, and Q05(line263):20stacks,
2–9players,7cash rake profiles, BBante,MTTchipEV, specified sizes. Neither is the
complete20-profile/sizing registry. See spec-provenance.json and history-scan.json.
920unique reachable text blobs under docs/gto/handoff were inspected within1s,
no oversize/timeout and no literal20-stack list found. Encoded/external original
archives are not claimed searched or recovered. Synthetic2..40 smoke fixtures
and researchHU50/2.5/9/21/50 are not substituted for formal numerical requirements.

Unresolved numerical inputs: the20 stack values and per-format/seat assignment /
equal-or-unequal/before-or-after-ante semantics; complete open/3bet/4bet size sets
per stack/position/history, raise-to conventions and all-in handling. The original
formal real-game accuracy/EV acceptance tolerances also remain unestablished;
0.1BB is a research criterion, not silently a formal full-game threshold.

## Generate actual release candidates

Run from repository root with Node24:

    node scripts/gto-release/build.mjs src/gto/independentResearchData.json docs/qa/suit-exact-preflop-20261106/results.json /workspace/NEW-candidates.json

Output uses exclusive creation; no registry or existing file is overwritten.
The package contains8actual pre-existing context/model candidates,1352rows. It is
not eight new strategies. Every candidate stays BLOCKED_UNVERIFIED, draft
 equilibriumVerified=false; ordinary registrations0. Full output is reproducible,
not copied into Git a second time. candidate-summary.json pins each output digest.

The adapter requires the complete14196-value preflop policy from original solver
evidence, not only a UI export. It reconstructs every frequency by original tree
node/hand/action, recomputes f64LE policy SHA256 and compares independent-evaluation
before/after digests. The published fs.digest JSON identity uses a DIFFERENT
encoding; both identities are retained explicitly, not equated or overwritten.
The complete policy identity additionally binds the frozen continuation digest.
Source/export metadata, model reach mass, actionEV/intervals, weighted profileEV,
independent BR arithmetic and query/seat/history are checked and preserved.
Fixed-model BR evidence is reused; no1755-world evaluation or full learning rerun.

sealReviewedCandidate is an offline TRANSPORT boundary using a separate trusted
build-time review registry, never an uploaded assertion or an auto-generated
proof. It checks the candidate digest, independent full-game/EV evidence reference,
formal-condition review when applicable, certificate scope/query/policy and the
entire displayed payload digest. Real candidates have no such review and are
rejected. Positive tests use synthetic transport fixtures only, not GTO evidence.
This code is not an independent Nash proof engine or a release authorization.

## Search and integrity

Ordinary RFI/3bet display now uses WebCrypto SHA256 over normalized169rows,
frequencies, profile/actionEV intervals, action labels, query, schema and identities.
A structurally valid but coherently modified frequency/EV table cannot reuse an
old reviewed certificate. Existing narrowly defined HU1BB calibration is preserved
through its existing immutable evidence generator; ordinary missing-digest data
is refused. The synchronous legacy lookup is labelled structural-only and no
longer drives ordinary strategy display.

Async search clears results immediately, marks pending, cancels stale completions
on edits/history errors/toggles/unmount, and shows a recoverable verification error.
ActionEV/intervals display only when present and valid. Missing actionEV remains
absent, not0-filled. Dataset version and payload identity appear in evidence details.
No upload endpoint, network storage, production DB or catalog addition.

## Short DCFR diagnosis (completed and stopped)

Same two tiny games, genuine32-step CFR+ teachers, same simultaneous order and
new-mass weight.2×2regret/average-discount factorial, exactly16additional steps.
8.185606s,60s cap,2GiB reserve. R1S1 replay matches existing DCFR step R/S at1e-12.
At this endpoint regret discount changed NC by0 in both games; average discount
reduced NC by0.0002475703/0.0002759230BB. This does not explain the old128-step
ranking or show population improvement. No extra trial, adoption or long learning.

## Local verification

- Node41PASS across existing GTO suites plus8new release/integrity tests.
- Existing matched-history8Python tests preserve actual12checkpoints.
- Three browser scripts:26PASS at390px, including coherent data tampering,
  delayed crypto vs input edits, actionEV and verification-failure handling.
- npm ci/cache, build and lint exit0; unrelated existing warnings remain.
- Research tree byte check; release/source/history evidence hashes; diff check.

Browser commands use existing system Chromium through a temporary launch wrapper;
all page external requests remain blocked. No production accounts were used.
React checklist: unconditional hooks, request version in a ref, cleanup on unmount,
no crypto in render, labelled controls/aria-busy, immutable updates, conditional
EV display, no new runtime dependency or network waterfall.

Historical matched-history manifests are NOT rewritten. Numerical sources remain
byte-pinned. Only the two legitimately evolved UI/parser sources are checked at
fixed original25142ce in Git, with current versions pinned/tested by this new
manifest. Other unexpected historical source changes still fail CI.

Latest resulting-commit CI must be observed separately; these precommit receipts
make no claim about that future run. No automatic scheduler/resume is enabled.

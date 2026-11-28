# Active private-vector CFR+ → full-public streaming (research only)

Base: `7ff7687119976300f7775e88fdd3bb5e8b9522c7`, Draft PR120.
Formal acceptance remains 0/12. No ordinary registry/publication/prod operation.

## Implemented game and estimators

The existing active C++ CF kernel is unchanged. `stream_chance.py` connects it to
weighted public-board chunks, integrating **raw** private CF gradients before
simultaneous CFR+ clipping; average updates keep own reach. Every board has1081
private hands and1070190 ordered legal private pairs. Old64 CF refinements are
lifted across board classes, with owner observation history retained.

The native bounded tree has3923 nodes (old2939). Generic supplied raise-to support
is unioned with exact native legal actions in subsequent preflop responses;10.5BB
3bet and SB subsequent response now belong to this same game. Root remains12/99;
87raise omissions and off-tree error are NOT certified. This is not a formal size
profile. Unknown public histories retain legal protected Sparse responses.

`stream_sampling.py` retains every persistent R/A row across fresh banks, uses
cached causal private partitions and zero-copy C-ABI indices. `stream_features.py`
batches the exact old feature function in C++; no new private/opponent information.
Numeric update budget1.5GiB, persistent scalar cell cap10million, RAM8GiB host.
`active_resume.restore_prior` now decompresses the initial average array once,
not once per node. Both original checkpoint next steps are bitwise reproduced.

## Separate experiments, not pooled evidence

1. `stream-subgame-.../{seed}`: 13 exact-probability weighted board catalog,
   fixed throughout training. Finite-game controls only; not full NLH chance.
2. `public-stream-.../17120101`: independent fresh one-board/stratum updates.
   Target uniform52, finite catalog selection. Burn-in/variance pilot, not PASS.
3. `public-stream-final-.../{seed}`: fresh target-CDF systematic13-board bank on
   **every update**. Conditional uniform draws within each public stratum;
   board weight1/13; exact private integration conditional on that public board.
   Same full52 target as pilot, reduced root gradient variance. No fixed2board
   extension is presented as global convergence. New target starts from old
   behavior only (R/A zero); subsequent bank changes carry exact cumulative R/A.

Flop categories paired/monotone/connected × public paired-pattern give13 strata.
Masses enumerate22100flops and exact compatible turn/river classes, not heuristic
texture frequencies. Systematic CDF expected mass is checked by exact integration
over every allocation breakpoint. Draw/private removal and3player raw CF are
checked independently. A new refinement absent before sampling gets the declared
causal frozen-parent rule; a completely unseen known-node parent is uniform over
supported legal actions, explicitly UNVERIFIED. It is not a quality certificate.

Training/selection/final data are separate. Selection native seed17151201/1024,
selection catalog17153201+trainingseed. Final native seed17154101/32768, final
catalog17153301+trainingseed. Last iterate is predeclared for final diagnostics,
not selected from those final outcomes. Candidate-best and last remain separate.
A confidence interval containing zero is neither safety nor noninferiority.

## Independent bounds and limitations

`stream_measure.py` integrates all finite catalog/world CF values before each
information-set BR maximum. It is an independent depth-first oracle equivalent
to the old matrix oracle, reducing evaluation workspace. Fine-own/visible-board
information refinement yields exact per-player finite information gains and
`finite fine NC = coarse NC + sum(gains)` for the **same policy and catalog**.
This implements a finite error envelope, NOT a full52/native error bound.
Full native BR/NC upper, chance generalization, abstract continuation and omitted
size uniform upper bounds remain UNKNOWN. Native legal deviations are lower
bound witnesses only. Sampling histories do not prove entire-game safety.

## Recovery

Original bounded checkpoint.npz/initial.npz are preserved at
`docs/qa/active-subgame-20261127/{17120101,17120102}/bounded/`.
`legacy-replay.txt` records actual original source/build/checkpoint/initial hashes
and exact next step. Four pre-existing untracked priorities.json are not claimed
new recovered artifacts (raw originals were already losslessly archived).

New full-public checkpoints are lossless `*.npy.zst` shards, `identity.json.zst`,
`receipt.json`. Restore rejects altered source/build/feature binary/shard bytes.
Final per-seed `replay.json` checks next fresh public bank RNG AND exact R/A/visits
next update. No automatic restart daemon is claimed. Source/identity/artifact
manifests and Git commit must be checked before manual continuation.

Manual inspection (choose the actual checkpoint from result.json, never confuse
selection best with last):
```
from gto.qualification.public_stream_study import restore
from gto.qualification.public_stream_batch import catalog
from gto.qualification.stream_sampling import replace_bank
q, identity, rng = restore(checkpoint_directory)
next_seed = rng.getrandbits(64)
r = replace_bank(q, catalog(q.lib, next_seed))
r.step()  # complete atomic update; preserve q/rng state on failure
```
Use the driver replay transaction for failure rollback; this short example is not
an automatic resumable service. Never overwrite an old checkpoint directory.

Multiplayer IID vs target-CDF external sampling reuses existingN solver and
finite3 oracle.6/9 caps stay20000rows; cap failures rollback whole update and RNG.
No general multiway Nash convergence claim. See multiplayer*/results.json.

Full release target remains2–9players/20stacks/allpositions/modes/ante/rake/unequal
stacks. Existing approval proposal A1–A7 is unchanged and pending; no HU milestone
is called initial release. See acceptance.json and the existing20261125 proposal.

Fresh-environment prerequisites (read-only checks before any continued learning):
```
python -B -m gto.qualification.build --directory /tmp/native-qualification
python -B -c "from gto.qualification.sparse_solver import build; build('/tmp/sparse','/tmp/native-qualification')"
```
Python3.12/NumPy2.3.5, C++20 compiler andzstd are required. Restore strictly checks
build hashes; a different compiler/ABI build must not be silently substituted.
The original Sparse warm checkpoints remain required for legal off-tree serving.
A hash ledger alone is not a restored checkpoint: actual compressed arrays must
be present and verified. Original ZIP bytes from inaccessible sessions were not
recovered or claimed. No old session was waited on indefinitely.

## Completed final diagnostics

Both seeds completed64 fresh updates /832 unique training boards each. Pure
learning CPU839.352449 /758.217924 seconds. Selection NC4.487045→2.711073 and
6.667945→4.999185BB. These selection results are NOT heldout safety evidence.
Fresh final catalog NC3.792407/2.619999; fine-information BR/NC5.501572/5.791092BB.
These catalog values use a different chance law; no cross-game convergence claim.

Native fresh32768worlds perseed (same four policies, paired worlds/tapes):
SB EV−.060616[−.402383,.281151] /+.044123[−.296957,.385203]BB.
River-jam gain−.464249[−.884154,−.044343] /−.649384[−1.091424,−.207343].
Relative previous signed-last jam gain changes−2.811768 /−2.290909BB,
simultaneous intervals strictly negative. Relative previous active candidate,
jam change is NOT significant;8BB gain change−.772923[−1.529440,−.016407] /
−.905150[−1.678281,−.132019]BB is significantly lower. No global safety proof.

River true-trained regret/average query reuse98.7421/99.6251% and99.3252/99.5706%.
This is baseline-path queries only, not all forced-probe queries or a quality PASS.
Both seeds have507 exact Fold cells, versus338 under their old separate digests;
Jam proposal precision97/111 (old203/210 retained separately). Formal precision0.
All169 vs10.5BB posterior ranges are now nonzero in both seeds, so the old
169/169 UNKNOWN_ZERO_RANGE due omitted support is resolved. The missing Jam
precision here is sampling/work budget, NOT zero posterior. Other action EV and
full native BR/chance/continuation/size bounds remain UNKNOWN.

See ../public-stream-final-20261127/summary.json, same-digest per-seed native/EV/
range/BR receipts. Final data were not used to retrain, select or promote a policy.

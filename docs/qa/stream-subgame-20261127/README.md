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

# PCS private-vector implementation / 2026-11-25–26

Base af804c7a8173099fb737c2822fc872f8df6e737c, Draft PR120.
**Implementation/oracle gates PASS; HU native quality gate FAIL/UNKNOWN. Formal0/12, RFI0/3bet0.**
Full2..9/multistack first-release scope unchanged. No ordinary registry admission.

## What actually ran

New workspace clone, pwd/git/compiler response restored. Initial sandbox network
proxy failed; permitted network route worked. No old environment's non-Git DB/ZIP
was recovered. Source hash and decompressed bytes of BOTH compact sparse HU
checkpoints verified. Their R/A/RNG loaded into newly compiled binary; duplicated
new-build next batches byte-identical. Old binary hash differs, so this is explicit
migration, **not strict original-binary restoration**. Six/nine max both-seed actual
R/A/RNG/lazy parents/history also restored and next-step copies matched. See
recovery.json, multiplayer-recovery.json and restore-*.py.

Existing fullstreet_core.cc/fs_eval, sparse_native.cc, multiplayer_joint.py,
old8 candidates, all original CPs, frozen CFR/HU1BB remain unchanged.

## Solver change

- public_chance_core.cc includes frozen fullstreet core; adds a CSR evaluator
  (no4-action ceiling) and private-vector terminal integration.
- For each uniformly drawn complete public board, integrate all1081 compatible
  private hands and1070190 disjoint ordered pairs. Rank-prefix totals minus each
  own-card blocker plus same-hand inclusion/exclusion give exact conditional
  win/tie mass in linear hand/rank work per terminal. All future/private arrays
  remain evaluator-only; policy uses the same causal own169/private-feature and
  public-prefix indexes as the existing fullstreet joint game.
- public_chance_solver.Game uses one pre-update pi for both owners. No frozen
  range payoff: opponent reach is recomputed from current pi at every evaluation.
- Dense private-pair independent oracle checks mass, EV/BR, regret, own-reach
  average, conditional actionEV, unequal public chance weights and shared-prefix
  BR. A seven-action CSR case, tiny two-player convergence and exact CP replay
  are tested. Native regressions cover off-half-BB-grid minraise/allin/shortallin.
- private_integrated_joint reuses existing SparseJoint.collect with finite chance
  and opponent-proposal expectation **before clipping**. It is explicitly limited
  to the three-player oracle fixture. It is not a full-tree6/9 implementation.

## Preregistered gates and preserved protocol changes

Per-HU pilot: ~10 seconds pure learning,768MiB process working budget,100MiB
new QA physical storage, separate selection and final boards, fixed seeds.
First4/8-step gate stopped too early despite recovering seed1 trend: retained
in early-eight/ with exact driver-v1.py. Next gate uses disjoint data and permits
10 seconds; seed1 severe regression stopped at16, seed2 reached30. Both chose0.
Those artifacts and driver-v2.py are retained, not relabeled as new strategies.
Finally reuse actual old fullstreet R/A as arbitrary finite initial state; this
is **not an unbiased prefix of the new uniform-board law**. Reset new t/visits,
preserve old arrays, independent new split. driver-v3.py is the exact warm pilot
source snapshot; current driver adds synchronized best-RNG receipts for future
runs. Selection values are not independent final PASS evidence.

| warm seed | new updates selected | pure train s | timed best-update IO s | selection NC initial→best | independent final finite2board NC old→new |
|---|---:|---:|---:|---:|---:|
|17120101|24|10.078500|4.650055|11.243002→6.680655|8.396243→9.382136|
|17120102|22|10.181671|5.075704|4.322443→4.282608|4.365948→4.247004|

Exact curves are in warm/*/result.json.
The timed IO field excludes initial save/final policy export; it is not all IO.
Complete-iteration soft time overrun<=.182s. Peak RSS543154176/543072256 bytes.
No escalation: seed1 independent final worsened. Final tiny2board restricted BR
is a finite-game diagnostic, **not a full-board/full-native NC upper bound**.
Both new digests, all8 preflop contexts x169 frequency/actionEV rows per seed,
R/A/visits/RNG checkpoints and source/build IDs are stored in warm/. Conditional
model point EV is not a native169/action confidence certificate.

## Independent native final data

Fresh seed17135101,4096 worlds/seed, same frozen digest per raw/conditional run.
Existing conditional all-in estimator reused; raw native rollout retained too.
Two separate estimator families: each9 metrics x2seeds, allocated delta .001/24
per metric. Each family's simultaneous confidence is at least99.9%; no combined
99.9% claim over both estimator families or formal release profiles.

Conditional estimator (native-conditional.json):

| seed | SB EV BB (interval) | paired change vs old causal warm policy (interval) | turn new-CF+new-average reuse | river reuse |
|---|---|---|---:|---:|
|1|−.001360 [−1.376024,1.373305]|−.116526 [−2.187949,1.954897]|1173/1243=94.3685%|531/619=85.7835%|
|2| .112659 [−1.225227,1.450545]| .026010 [−1.354092,1.406113]|1709/1826=93.5926%|846/964=87.7593%|

Previous sparse both-R/average river reuse was0%/0%. These are different
abstractions/policies/query trajectories; reuse increase is engineering evidence,
NOT a causal strategic-quality claim. New-CF means new den>0 visit, not necessarily
positive regret. New average means increment beyond old warm A, threshold1e-14.
Raw rollout reuse514/599 and817/925 is also retained. No significant EV gain.
Raw EV interval widths3.420462/3.163330; conditional widths2.749329/2.675773BB.
Different raw/conditional action RNG transforms are disclosed; variance ratios
are descriptive, not a matched-trajectory variance proof or A7 precision PASS.

Conditional legal deviation mean [interval], BB:
- 3.5BB open:2.111559 [−1.256138,5.479256] /1.997540 [−1.370577,5.365657].
- 8BB open:2.037615 [−1.377126,5.452355] /1.923596 [−1.490675,5.337867].
- 10.5BB3bet:.516606 [−1.853876,2.887089] /.336824 [−1.741997,2.415645].
- River jam:−.096191 [−1.909855,1.717472] /−.461426 [−2.290643,1.367791].
- Nuts jam/fold probes also stored. Intervals include0; absence of significance is
not safety. Historical sparse3.5 improvement/data preserved, not replaced.
Complete native BR/NC upper, abstraction/continuation/omitted-size error UNKNOWN.
Existing measured33462 rootEV cells preserved; formal precision cells remain0.
New PCS uses reduced legacy preflop tree; it does not learn all99 legal sizes.
Existing sparse12/99support preserved. CSR capability is not coverage/certification.

## Three-player quality and six/nine continuity

Finite4world ordinary RFI/3bet + explicit postflop check/call game:
integrated32 sum unilateral gains7.243827→.023738945626BB,22.817561s.
Independent terminal-path regret/average oracle agrees at2e-11 and state/RNG
resume matches. Same-budget sampled controls22.8186/22.8191s,2518/2685steps:
.123053225/.093164709BB. Integration improves this finite fixture, while the
pre-existing vector exact solver is still preferable when its whole tree fits.
Do not extrapolate this enumeration to6/9 or claim general multiplayer Nash
convergence. Six/nine policies and checkpoints restored, quality not newly proven.

## Cost and release feasibility

Same884nodes/board/uniform pi microbenchmark, EV/BR agree to~2e-13:
- Already aggregated dense: block .044847s, owner .084289s,RSS349454336.
- Physical dense1081 hand: owner .633612s,RSS429645824.
- Integrated1081 hand: block .005520s,owner .102119s,RSS379748352.
Physical pair integration is ~6.2x faster than uncompressed dense evaluation,
**but ~21% slower than the existing aggregated kernel on this coarse key**.
No end-to-end speedup claim. Richer information maps need this tradeoff retested.

Frozen seed1 policy compressed12332227bytes; build2.423609s/load .577470s;
1000 root cached-row lookups median12.0735us/p9515.918us. This is Python in-process
lookup only, NOT web/search/on-demand solve SLA or quality proof. Seed2 policy
17330807bytes. Whole new QA~81MiB after SHA-identical relative-symlink dedup;
initial102MiB transient budget overrun disclosed, original evidence untouched.
No all-stack enumeration. Example proposed400 stack values imply400^9 vectors;
exhaustive precomputation is not a feasible release design. Candidate architecture:
common certified offline blueprints + exact-game/config/digest cache + range-
conditioned local solving for misses, with explicit error budgets. Current solver
cannot yet certify such misses: latency, precision and total free compute required
for full first release UNKNOWN. No numerical extrapolation of10-second pilots
into qualified full-release cost/ETA. Unknown requests must remain NOT_QUALIFIED,
which is a development blocker, not a reduction of the release requirement.

## Reproduction and manual restart

From repository root, network only needed for pinned build dependency:

    python -B -m gto.qualification.build --directory /tmp/native-qualification
    python -B -m gto.qualification.sparse_solver --build /tmp/sparse --native-build /tmp/native-qualification
    QUALIFICATION_BUILD=/tmp/native-qualification python -B -m unittest gto.qualification.test_public_chance gto.qualification.test_private_integrated_joint gto.qualification.test_fullstreet gto.qualification.test_multiplayer_expanded -v
    python -B -m gto.qualification.public_chance_resume --root docs/qa/public-chance-20261125 --seed 17120101
    python -B -m gto.qualification.public_chance_resume --root docs/qa/public-chance-20261125 --seed 17120102

Resume verifies source snapshots/build/parent/checkpoint digest and best RNG,
then repeats one next-step from two restored copies, comparing R/A/visits/t/RNG.
Both actual new checkpoints PASS. No automatic restart service. Before a new
pilot use a NEW output path, explicit new --split-offset, independent final native seed/data and frozen protocol;
do not overwrite these QA files or reuse final data for candidate selection.
Study/helper source snapshots are retained to reproduce historical pilot hashes.
Final targeted regression:32 tests PASS19.737s, including8 new tests.
Initial short-allin test expected the shorthand3 instead of native returned raise-to9;
fixture corrected, then final32 tests pass. No production rule was changed.
No new UI/browser/npm tests applicable (Python/C++ offline only).

## Formal decisions / next quality gate

acceptance.json retains all12 original conditions false,0/12; no quality threshold
relaxed. Review proposals (20stack,2..9allpositions, MTT/ring,BBante0/.5/1,
realistic caps, unequal inputs) remain PENDING in the existing approval document.
Pinned rules currently reject0.5BBante and new realistic cap candidates; a new
research rules version plus independent native/reference verification is needed,
not silent adoption. Next: information-richer sparse indexing for the integrated
vectors, exact-conditional oracle/error tests, generic adaptive support + learned
off-tree continuation, independent native BR/error and all169 conditionalEV gates.
Full HU-quality/precision/bounds,2..9profiles and formal specifications block
release. No main/prod/SQL/DB/Storage/Vercel/SSO/fees/forcepush/destructive operation.

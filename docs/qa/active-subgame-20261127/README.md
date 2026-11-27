# Active private-vector / bounded-native gate (2026-11-27)

Research only, BLOCKED_UNVERIFIED. No registry admission or public product change.
HU50 is a milestone, not the required 2–9 player / 20-stack release.
Base: 20057f4d4ef5e69ad76e53132eb8651768981cb2, PR120 remains Draft.

## Implementation and acceptance gate

Reuse PCS exact private integration (1081 hands / 1070190 ordered legal pairs),
CSR public actions, native ledgers and simultaneous-owner CFR+. Only row addressing
changes: active (node, board, own hand) offsets replace unreachable dense rows.
The independent original kernel must agree on EV, BR, raw regret, own-reach average
and CF mass before learning. No four-action array or action probability truncation
is introduced by the active kernel. Old sources/checkpoints are unchanged.

Refinement priorities are one-step CF-value Jensen gaps in finer observable cells.
The 64 highest cells are split by made category/primary rank, flush/straight draw
potential, public suit counts and private blockers. The predicate is fixed during
learning, is suit invariant and sees only own cards/current public prefix.
All earlier selected owner observations are remembered in later infosets.
Priority sums are NOT native error upper bounds. Warm mass is apportioned among
children by chance occurrence count; this preserves behavior and total R/A mass,
not the historical split counterfactual regrets.

Native bounded tree: 2939 nodes, root native actions
[0,1,6,7,8,9,10,12,16,18,19,102]. Thus existing 12/99 support is retained;
the previous 884-node PCS tree offered only [0,1,8]. Raise action a means
raise-to (a−2)/2 BB. Later raises retain exact public history and native legality,
short all-in/reopening and native settlement; no nearest-action history mapping.
Postflop remains an internal bounded model, with existing street_tree actions.
It is NOT all legal postflop actions, nor proof that omitted actions are harmless.
The other 87 root raises and omitted downstream actions remain unqualified.

Initial projection receipts record removed probability mass and zero-mass rows.
They describe initialization only, not an equivalence between full native and
restricted games. New CFR frequencies are optimized on the offered joint tree.
Unknown native histories use the preserved Sparse controller. Unseen feature
cells use chance-weighted parent averages; both are explicitly counted, never
silently completed with fold, and neither is a strategic safety certificate.

## Experiments and limits

Two immutable modes per seed, each 30 then90 CPU seconds; no unconditional long run:
- refine: transfer the previous exact 884-node checkpoint, preserve its policy,
  split64 parents and retrain. Initial reduced NC may rise because BR gets more
  information; EV must remain unchanged before the first update.
- bounded: initialize from the preserved coarse native controller and jointly
  train all12 root sizes with their downstream responses, rather than project
  learned full-size probabilities back onto the old3-action root.

Both modes keep the old fixed2-board law so comparisons remain reproducible.
Both boards are unpaired. This is a substantial chance/texture coverage limit,
not a representative full-NLH solve. `identity.parent_sha256` is the original
same-game board/control checkpoint reference; in bounded mode it is NOT the
initialization policy checkpoint. Initialization is audit.make(seed, coarse=True),
whose old Sparse raw hash/source checks remain in effect; see provenance.json.

Physical BR preserves the previous exact-own-card/visible-board benchmark on
this finite law. The separately labeled fine suit-orbit BR uses canonical own+
visible-board observations (preflop169), and retains owner observation history.
It corresponds to orbit-closing the finite board law, not integrating NLH ranks.
Suit symmetry is verified by explicit24-permutation response-score enumeration.
Do not replace the old physical metric with the smaller suit-orbit metric.
Neither is a full-native BR upper bound.

8192 fresh native worlds (17140901) compare all four predeclared controllers.
The full-support bounded controller is separately confirmed against protected
Sparse and prior signed-last on32768 fresh worlds (17141901), with no retraining,
no pooling, no selection on the confirmation data. Paired common worlds/action
RNG and conditional all-in integration reuse existing variance reduction.
Family confidence99.9%,100 preallocated events across both seeds per receipt.
No nonsignificant probe is a safety proof. Native coverage in the8192 receipt
is measured on baseline paths separately from probe paths. Indexed rows are
NOT automatically called learned: average mass/regret must change from initial.

## Reproduction / recovery

Run from repository root with native build in /tmp/native-qualification:

    python -B -m gto.qualification.active_study --seed 17120101 --mode refine
    python -B -m gto.qualification.active_study --seed 17120101 --mode bounded

Use a fresh output root to reproduce; existing artifact directories fail closed.
Repeat for17120102. The exact executed source is also copied under source-v1.
The deterministic kernel uses no sampling RNG; complete board law is pinned.
Training CPU seconds exclude setup, source compilation, checkpoint I/O and BR.
Actual setup/fine-oracle RSS is much larger than numeric kernel estimates; see
result.json peak_RSS_bytes. Current host quota2 CPU /8GiB, no paid resources.

    from gto.qualification.active_resume import restore
    q, identity = restore('docs/qa/active-subgame-20261127/17120101/bounded',
                          '/tmp/active-resume')
    q.step()

Both checkpoint.npz AND initial.npz are required and SHA-checked. initial A
encodes the warm prior used if positive regrets vanish; R/A-only reconstruction
with uniform prior is insufficient. Source/build and fixed boards are checked.
Each replay.json checks a next step from TWO independently reconstructed objects;
nextstep-proof.npz is a proof checkpoint, not the selected90-second policy.
preflop.json exports169 hands each for RFI / facing3BB / facing10BB3bet on the
SAME saved policy. Its EVs are exact conditional finite-board/action EVs, not
full-NLH EV intervals or formally qualified precision cells.

Old8 candidates/frozen/HU1BB/checkpoints remain unchanged. Accessible actual
NPZ/RNG bytes for the four earlier same-game controls were hash-verified.
Old inaccessible sessions/ZIPs are not claimed recovered. No automatic future
restart service is installed; recovery requires running the documented command.

## Formal release blockers

All12 conditions remain unpassed; formally verified RFI0 /3bet0 /EV precision0.
Old33462 root measurements, Fold1014, Jam493 and new-digest Jam196 stay separate;
none is added to the present digest's formal count. Complete native BR/NC upper,
uniform continuation/chance/abstraction/omitted-size errors remain UNKNOWN.
Finite-game exact BR differences do not establish a native transfer bound.

3-player exact gain0.023738946BB and K4 oracle, existing6max/9max2seed research
policies are protected. Native N-seat reach/chance/sidepot/refund/ante/rake/unequal
stack regressions pass; no new multiway quality gain or general Nash guarantee
is claimed from this two-player private-vector kernel.

Next engineering gate: stream stratified public-board batches into the same
active private-vector kernel, integrate signed CF updates before clipping, cover
paired-board/nut/blocker cells, and compare with independent native data before
extending training. Retain12-size joint support and add sizes only from separate
discovery evidence with downstream training. Full release compute/cache-miss
latency and certified-resource requirements remain UNKNOWN; these limited CPU
curves are not a completion estimate or an app response-time measurement.

Approval proposals A1–A7 remain pending, unchanged in
GTO_PREFLOP_RELEASE_APPROVAL_AND_EXECUTION_20261125.md. No specification adoption,
criterion relaxation, production/SQL/merge/deploy or successful-CI rerun occurred.

## Measured results

| seed |884 refined NC (90CPU)|884 physical BR NC before→after|2939 NC initial→90CPU|2939 finer physical BR NC|river updatedR/A reuse|
|---|---:|---:|---:|---:|---:|
|17120101|0.029835|1.057948→0.726250|11.379261→0.167217|1.188915|36.7670%|
|17120102|0.035427|1.058656→0.750544|5.790538→0.141411|1.241698|40.2673%|

32768-world native confirmation (99.9% family intervals):

- 17120101: SB EV 0.057045 [-0.21793919727748684, 0.3320282383227046]; BB river-jam gain 0.208572 [-0.3535652417445142, 0.7707100171351392]; paired difference vs prior signed-last -2.117310 [-2.980137251748502, -1.2544818888764981].
- 17120102: SB EV 0.068189 [-0.229409625890013, 0.3657874421384347]; BB river-jam gain -0.202789 [-0.6420244420349974, 0.23644582875374742]; paired difference vs prior signed-last -1.767273 [-2.500838268933755, -1.0337076295037446].

Both known river-jam weaknesses significantly decreased relative to signed-last,
but neither native EV nor jam resistance significantly improves over protected
Sparse. Do not attribute fallback performance to learned-row quality. More than
half of independent river queries still back off; further learning on the same
two unpaired boards is not justified as a native quality breakthrough.

Per current digest: exactFold338 and proposedJam203/210 (seed1/2 respectively).
All169 vs3bet10.5 EVs are UNKNOWN_ZERO_RANGE in both seeds; probabilities are not
patched with arbitrary beliefs. Finite-law vs10BB EVs are exported separately.
No cross-digest count summation, no formal precision PASS.

The post-run driver vectorizes warm initialization:2939nodes/1075859action cells
in0.170626CPU /0.170918wall seconds, excluding construction/learning/app latency.
Executed driver and resume sources remain under source-v1 with exact SHA pins.
Only that archived driver is accepted on old-bundle replay; core/policy sources
and binary must still match. All four new bundles replay a next update exactly
from independent reconstructed objects.

Priority diagnostics are stored as lossless priorities.json.zst archives; their
original raw SHA values and byte equality checks are in priority-compression.json.
The raw files remain in this workspace and are not deleted. Decompress with zstd
when needed; checkpoint/identity/EV receipt paths used by loaders remain unchanged.

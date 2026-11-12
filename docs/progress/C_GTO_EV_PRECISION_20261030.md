# HU50BB fixed-policy EV precision
Start public58f2d7d5b578b1eed6377c864cc6849f517d93bf/local158748d7548e26eb62ac2a4cf4b8ba9da131dae4,
clean matchingtreef2f50ad078019ccccf0800a126b468483bc99efa. Saved kernels and
full policies available in/workspace/gto-abstract-canonical-fp. Prior CI754PASS.
Acceptance BEFORE edits: reuse frozen seed1701 policies and independent700017
kernel; enumerate all compatible opponent TYPES and public preflop branches
with exact blocker/posterior mass (floating aggregation, not claim exact real
poker EV). No CFR retraining or larger sample budget. Separate exact fold costs,
future sampled leaves, conditional weighted Hoeffding and a valid stratified
second-moment/Bernstein bound, preserving shared-plane correlations via Jensen.
Split failure budget across every model/history/hand/action/profile and across
intersected bounds. Keep real-game approximation error UNKNOWN. Verify independent
CF evaluation, probability/coeff conservation, finite exact enumerated oracles,
interval accounting and fixed-policy/checkpoint/source identity. Compare exact
turn/river enumeration on explicit hole/flop slices; do NOT generalize slice
precision to169ranges. UI may use only labelled independent model EVs/intervals;
8research ranges/HU1BB/native2..9 tests maintained. Trusted matching reference
not currently available: comparison remains UNPERFORMED. Formal12 evaluated
against full stated conditions, not coverage alone. No production writes/deploy/
main/fees/otherPRs. CI only for actual changed implementation/regeneration.

## Implemented evidence (2026-10-30)
Frozen input packet committed in docs/qa/ev-precision-20261030/frozen-inputs.json:
lossless integer moments and complete policies with SHA256 verification, no CFR
iterations added. No MC sample increase:256 per unordered class pair,seed700017.
Policy-only allocation selects AA/KK/AKo/AKs before reading validation outcomes.
2210 suit-canonical concrete matchups enumerated over1712304 boards each;
1611/28561 all-in cells and2287/142805 payoff entries exact (including symmetry).
Other sampled private-hole/flop states integrate all990 turn/river pairs, preserving
original shared worlds, seat pairing and controller semantics. Observed variance
ratio .3160(all-in),.4769(flop), not a claim of real-game approximation accuracy.
All opponent classes and action branches enumerated with posterior history mass.
4056 conditional action EV points agree with preserved native CF evaluation.

Pot-specific payoff caps100/4/10/36/84chips, shared-plane covariance-safe
second-moment Bernstein/Hoeffding; failure .0025 per model for all action/profile
intervals and .0025 per model for all BR terminal bounds. Union failure<=.01
across both models and BOTH families. Global belief-MDP BR respects information
sets; independent native BR agrees within1e-10. Maxima taken AFTER uniform leaf
bounds, avoiding the local-improvement-as-equilibrium-certificate error.
Fixed-controller expected-game NashConv99% simultaneous bounds:
checkdown[0,.1520740834]BB,flop[0,.2801729427]BB. Point estimates .0048135714 /
.0074888430BB. No accepted convergence tolerance or real-game certificate.

Worst conditional PROFILE radii per context,checkdown/flop(BB):
RFI .129515/.217853;vsopen .288650/.435833;
vs3bet1.008973/1.175466;vs4bet3.719171/3.260014.
Worst ACTION radii .161401/.232393,.453492/.435898,
1.164118/1.366227,4.397145/3.491035 respectively.
Previous coarse18.311302BB replaced in8 research ranges;1352profiles/4056actions,
16profiles and1388actions have no sampling uncertainty within the fixed model.
Actual real-game approximation error UNKNOWN; matching reference comparison
UNPERFORMED/difference UNKNOWN. Formal0/12 remains; ordinary verified ranges0,
research8 and existing HU1BB1 preserved. Full acceptance reasons in
../qa/ev-precision-20261030/ACCEPTANCE.md. No formal stack/size source invented.

Local precision9PASS (20k rank samples, exactrunout oracle, posterior, covariance,
immutable input checks,4056actions and global BR independent evaluator);
Node16PASS. New CI regenerates enumeration/EV export from committed inputs,
with original1e-12 numeric comparison and strict source/policy hashes.
Local original/public metadata differ but share starting tree; preserve both
histories and publish a fast-forward commit parented to public58f2d7d, verify
resulting tree equals local commit. No reset/force-push.

## Resume
Check current HEAD,dirty files and latest4 CI workflows before doing new work.
Reusable kernels /workspace/gto-precision-enumeration/*expanded*; cheap rebuild
/workspace/gto-precision-reassemble.py; portable rebuild via workflow
.github/workflows/gto-ev-precision.yml. Next: remaining high-depth EV uncertainty,
calibrate fixed continuation against trusted matching reference; evaluate
abstraction fidelity before any formal release. Reference unavailable is an
explicit validation gap, not numericalzero. No production/settings/main/fees.
AUTO-RESUME and independent automatic restart: absent.

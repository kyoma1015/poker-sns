# HU50BB EV origin and missing-policy sensitivity audit

Starting public b9852e0099f2019a5faaebad469ca8d80415736c/local70b99a2,
identical tree9e5547d55ee11ea9e2b3245ce492a1f4dbb1d3d2, clean working tree.
Acceptance: independently reconcile chip EV (before posting blinds), no duplicate
SB/BB subtraction, actual terminal rank/ledger, explicit missing completion
sensitivity, same10000response training budget and held-out12000worlds. Preserve
HU1BB evidence/original3sources, strict partial-policy null EV and UI gates.
No formal acceptance change without whole-game evidence. Scope only GTO.

Independent Python terminal oracle: derives invested chips from initial minus
remaining, verifies live/dead ledger, derives fold award or matched HU pot and
uncalled refund, independently ranks all21five-card subsets at showdown. Does
not call native rank/returns/settlement to derive expected payoff. Restricts
itself to explicit HU no ante/rake; existing multiway/rake tests remain separate.
Audit compares both native settlement and returns at every held-out terminal.
Net is measured before forced blinds: initial fold SB=-1chip=-0.5BB, BB=+1chip.
After RFI5chips versus BB18chips, SB fold=-5chips, not -6; BB uncalled excess is
not a second loss. Pure fixtures cover blind/raise-fold, refund/tie and categories.

Sensitivity keeps observed learned rows unchanged, varying only missing rows:
uniform, SB check/call, BB check/call, both check/call. Same12000worlds/actionseeds;
whole-profile EV and paired differences with99% simultaneous intervals across
four profiles/two statistics. BB changes are NOT unilateral SB gains. This
isolates completion dependence but cannot certify original partial policy EV.

Response comparison holds native game/action space/opponent/seed/budget fixed.
Control uses original utilities; treatment subtracts known initial-fold value
(-1chip), making fold utility exactly zero. Constant utility shift preserves
expected regrets/optimal policies; finite-sample importance estimators/baselines
can differ. No assertion of variance reduction or convergence until measured.
Configuration/checkpoint contracts bind utility origin; raw held-out evaluation
ALWAYS uses original pre-blind net. Actual checkpoint/RNG restoration and same
12000sample full replay required for both experiments. No new iterations.

Print actual missing private ordered card pairs at100000 for vs4bet diagnosis;
never fill them with learned labels or treat coupon coverage as convergence.
Tests and CI evidence appended after actual execution. Native runtime absent
locally; pinned existing Actions reconstruction is the native execution path.
Local pure suite: python -B -m unittest discover -s gto/tests -v:51PASS.
No production DB/Storage/deploy/main/billing or independent restart changes.

2026-10-29 resumed: initial local0122576/public1cb11b659e14211c98410b716b6415f797a30b94
(tree14df20eb51b32b31adb891868632dd9aa967883a) preserved and published with
expected-head lease, no force. UI40832237550 SUCCESS; native40832237529
reconstruction/3-variant new tests PASS, full study in progress at this note.
Strengthened independence: replay raw public betting history from initial forced
blinds, calculate check/call and raise-to debits across streets, compare actual
remaining/folds before deriving terminal net. Native audit balances alone cannot
prove correct charging. New negative fixture catches matching live/remaining
ledgers that both charge a wrong SB blind. Added SB/BB pre/postflop completion
usage counts; this is trajectory diagnosis, not learned infoset coverage. Pure
suite now52PASS, local10Node checks PASS. Further native evidence pending.

First full CI1cb11b: native40832237529 SUCCESS676unittest+25Packed; UI40832237550
SUCCESS17; total718PASS. Independent audit48000sensitivity terminals plus
48000control/replay and48000centered/replay:144000terminal checks. Original
control policy/global moments/trajectory unchanged from b985. Separate exhaustive
Python5card oracle2598960hands/7462rankclasses matches known category counts.
SensitivitySB-only check/call missing completion:meanEV-0.190083BB,
99%simultaneousCI[-2.004388,1.624221]; unilateral gain3.146583BB,
CI[1.186385,5.106782]. BB-only change benefitsSB3.328792BB but is NOT a
unilateralSB gain. Both change3.592917BB, likewise not a unilateral response.
This detects a real dependency on missing completion; no blind double charge
found in this run's terminal ledger. OriginalpartialEV remains unspecified.
Centered learner gain-0.628625BB,CI[-3.018535,1.761285], variance1654.542730BB²
versus ordinary learner1653.300074BB²: neither improvement nor variance reduction
proved; do not adopt it. Seed29vs4bet missing pairs[20,6]73o,[26,10]84s,
[39,15]J5s,[43,8]Q4o. Rows remain missing, not backfilled with prior as learned.
Latest2ddd5d native40832558489 executing fuller debit replay/usage localization;
UI40832558684 SUCCESS. Results will be retained even while next experiment runs.

Next acceptance before exact-fold-control implementation: preserve all3original
modules/targeted module. Separate source-pinned generic solver hooks only:
read exact PUBLIC-history fold value before mutable action application, seed
that action's existing baseline before unchanged sampled(child-baseline)/q
correction. No sampling/regret/average equation changes or action pruning.
Known fold action-value estimate has zero conditional fold-draw variance; this
does not guarantee every regret/profile/gain estimator has lower variance.
Use uncentered original chip utility and same10000iterations/seed701/12000heldout
worlds. Exact source SHA participates in source-specific checkpoint contract.
Test actual2action numerical regret oracle across both draws, disabled-control
original updates, native HU fold versus declared public-history value, checkpoint
continuation/RNG; then run actual full HU comparison and full replay. Pure53PASS.
Formal0/12/ordinaryUI0 unchanged; future accuracy needs a valid full-game upper
bound, not a feasible gain lower bound or these partial frequency counts.

Exact-fold oracle cases also cover real postflop decisions: after limp/check,
flop BB bets10chips and SB folds, exact SB net=-2chips; after flop BBcheck,
SBbet6/BBraise14, SBfold exact net=-8chips. Previous-street investment must
remain charged once; no postflop showdown substitution or future-card peeking.

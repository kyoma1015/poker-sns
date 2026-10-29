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

# Expanded finite multiway native gate — declared before outcomes
Source d1ce78882afa9624d78cd48cdcfee3dc9f522e10. Metric verified strategies remains0.
Existing Joint and OfflineProfile reused; no newsolver family or oldCP overwrite.
Default legacy all-in scope remains available for existing tests/checkpoints via
original Git source; changed raw sourceSHA intentionally rejects oldidentity.

First: exact3player NativeGame stacks[24,22,20]chips (12/11/10BB), four explicit
AA/KK/QQ hole/board worlds, positive equal chance mass, no blocked cards reused.
Finite native action menu: fold/call/check plus3BBopen,10BB3bet then legal shove;
when a requested target exceeds stack, allow only actual legal short/full shove.
Preflop response chains continue until native finishes betting. Matched calls then
execute REAL native allstreet states, with explicit single check/call continuation.
This is a finite action/continuation abstraction, not fullnative NLHE/alllegal sizes.

3player build<=5000nodes/30sec; exact pathCF/average and lawfulhiddenworldBR must
match, clairvoyant perworldmax must not be called BR. Test handderived cashflows,
cardremoval/ownpublic keys, allstreet paths, shortallin, BBA/rake/unequalstacks,
true R/A/checkpoint continuation. Up to32frozen-piN-owner CFR+steps, no HUzero-sum
convergence guarantee. Pilot<=30sec per configuration; save curveR/Aidentity.
Only after correctnessPASS,6/9players build<=2000nodes/10sec each, fourworlds,
explicit unequal stacks/BBA/rake, up to8steps if treecomplete. On cap: record
BLOCKED_INCOMPLETE_TREE, no partialgame policy/BR/convergence result or checkpoint.
Overall localcompute~120sec, memory512MiB, QA20MiB. No allpopulation training,
normalregistry writes, spec adoption, prod/main/deploy/SSO/fees/destructive ops.

Additional build-only probe approved BEFORE execution (parent request): one6max
20,000node/10sec constructor attempt, external12sec wall/RSS256MiB watchdog, no
training or partialtree evaluation. Save separate6max-build-probe.json; original
2,000cap results/checkpoint stay unchanged. Budgetadditional<=20sec. Only consider
9maxbuild if6maxcomplete and a conservative resource estimate fits same limits.
If6maxexceeds20,000nodes,9maxcontains its entire publictree in the branch where
extra seats6/7/8 fold: same blinds/ante and first6stacks; hence9maxalso>20,000nodes.
This lowerbound uses a legal subset only, not a generated9maxpolicy or inference
that extra seats may be fixedfold in the full solver. No such policy is adopted.

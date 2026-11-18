# B — HU50 preflop implementation route (research only)

Metric: **verified app strategies0**, formal acceptance0/12 unchanged. No ordinary
registry or search catalog was modified. This folder is a generated comparison
candidate and integration preparation, not a released strategy or quality proof.

## Concrete shortest implementation found

The existing `gto.abstract.model/core.cc` already supplies class-conditioned CFR,
information-constrained BR and actionEV export. Existing native Betting supplies
legality and chip settlement. Replacing these engines would add adapter work
before addressing the actual missing native accuracy/continuation bounds.

New `preflop_release_solver.py` reuses them to generate HU50 RFI/vs-open/3bet:

- exact ordered compatible-combo counts, total1326*1225; no independent-hand
  approximation or blocked-card reuse;
- native-legal reduced raises3BB/10BB/50BB, both SB and BB responses, limp branch;
- all169 starting classes at RFI/vs-open/vs3bet/vs4bet;
- full52card/rank equity sampling, seed18118051,2worlds/class-pair, fixed100CFRiter;
- explicit forced-check continuation after matched preflop calls in the MODEL.
  Total provider explicitly check/calls postflop if deviated against. This is a
  restrictive continuation policy, not an assertion that a call ends the real game;
- exact unknown-preflop history uses the unchanged frozen full-history fallback,
  never nearest-size translation or implicit fold. Thus off-tree actions remain
  defined legally, but their quality is unverified.

Generated in4.4404sec (kernel1.1396sec, solve0.2515sec), without external engine or
strategy-data import. The sampled restricted-game profile SB EV=-0.045353BB,
BR_SB=0.023908BB, BR_BB minimum SB_EV=-0.102892BB,
restricted NashConv=0.126800BB. These are measurements of the sampled abstraction
ONLY; even that100iteration solve is not claimed converged. The2sample kernel is
not a sufficient all169/action confidence certificate.

Policy digest **bd46861da4c8c4eb786602315056092c5d253fd3d449b5183b01b96c5b2cc8f4**.
Only provider/iteration/suit metadata and source identity were adapted after the
fixed solve and before independent native evaluation; numeric strategy unchanged.
Parent A owns the predeclared independent native holdout and any subsequent EV
measurement. No additional B training or data-dependent strategy selection occurred.

### Unresolved errors — not hidden by abstraction convergence

Real-game continuation error, omitted-action error and complete native BR upper
remain UNKNOWN/null. Native full-policy NashConv is UNKNOWN. Private class-pair
chance counts are exact; payoff expectations are sampled. A native/selfplay result
cannot alone bound best-response changes caused by postflop betting or off-tree
preflop sizes. No physical100BB upper is used as convergence evidence.

`research-export.json.gz` prepares four169-row stages with actions/frequencies/
model actionEV and the same policy digest. It is deliberately `registry_ready=false`,
`ordinaryCatalogAdded=0`, `format=PENDING_FORMAL_SPEC_APPROVAL`; existing registry
must not treat it as a verified profile. It does not overwrite the8old candidates.

Current blockers: formal condition approval, full native deviation bound,
continuation/action-space error, true-game all169/actionEV precision, sampling
uncertainty. All formal12conditions remain mandatory. HU50 zero-ante/zero-rake
research does not adopt the20stack/size/MTT/ring/rake/ante proposals.

## Engine/data license comparison (primary sources pinned)

See `license-evidence.json` and copied primary LICENSE texts. No third-party engine
code or strategy chart was incorporated into the implementation. Rights to engine
software are **not** evidence of rights to unrelated strategy datasets or proof
that generated outputs are GTO. The search is a scoped comparison, not a claim
that no licensed preflop data exists anywhere.

| route | actual rights/scope observed | adaptation cost | decision |
|---|---|---|---|
| existing local Betting + CFR | preserved project sources, no new third-party import | working prototype in this folder; existing row/certificate schema reusable | fastest implemented generation path; native quality still blocked |
| OpenSpiel generic CFR | Apache-2.0; keep license/notices/modified-file notices; warranty disclaimer | new game/state/chance/action adapter and native payoff/BR parity tests; not a ready HU50 chart | plausible independent solver/oracle, not immediate verified data |
| OpenSpiel universal_poker | Apache wrapper calls external ACPC | ACPC dependency rights and exact configuration need separate verification; do not infer from wrapper license | conditional, not selected |
| RLCard | MIT software, retain copyright/permission notice; no warranty | no-limit implementation offers fold/check-call/half-pot/pot/all-in; needs3BB/10BB/all-size adaptation and payoff/action parity | no direct replacement; documented pre-trained CFR is Leduc, not verified HU50 |
| postflop-solver | AGPL-3.0-or-later per README/LICENSE; commercial use allowed under obligations, including applicable source/network provisions | postflop-only range/tree adapter, compliance design, range-conditioned continuation validation | possible continuation component, not preflop dataset or immediate drop-in; not imported |
| PokerHandEvaluator | Apache-2.0 evaluator code | rank adapter/oracle only; existing rank already present | no strategy generation benefit by itself |

Verified, applicable, redistributable HU50 RFI+3bet strategy datasets found in
these checked primary sources: **0**. RLCard's documented Leduc pretrained model
is a different game. Postflop engine algorithms and an evaluator are software,
not charts. No commercial/rights-unknown GTO charts were downloaded or reused.

OpenSpiel universal_poker README points to ethansbrown/acpc. At checked upstream
pin, repository metadata has no recognized license and sampled game.h gives a
copyright notice without a grant; common LICENSE/COPYING locations were not
found. This is an unresolved clearance item, not a conclusion that the entire
upstream can never be used. Generic CFR + our own Betting avoids that dependency.

## Remaining shortest release path

1. Keep this reduced generator as a bounded comparison model; use independent
   native evaluation to reject obvious weaknesses before more compute.
2. Supply a range-conditioned postflop continuation with quantified native error,
   and bound deviations over omitted legal raises/public histories. A stronger
   abstract solve alone cannot supply those bounds.
3. Freeze one digest; independently validate full native BR/EV/actionEV precision,
   correct legal off-tree responses and source/integrity certificates.
4. After formal specification and existing12conditions pass, convert the prepared
   rows through existing reviewed-certificate/registry/search code. No bypass or
   acceptance relaxation is needed or implemented.

There is no defensible calendar promise for steps2–3 from these short experiments.
Switching to a permissive engine does not remove their mathematical requirements.

## Focused tests and resumption

`QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.preflop_release_tests -v`
**5 PASS**: every abstract action replayed against native State, all169 rows legal
and normalized, unknown3.5BB history identical to frozen fallback, explicit
postflop controller, preserved identity/blockers. These tests are not GTO admission.

Load generated total policy:
`preflop_release_solver.load_policy(build_dir, strategy_path)`.
It supports `.row(o,True)`, `.provider(o)`, `.policy_digest`, `.id`, `.iteration`.
`.rows={}` is intentionally not a full-native trained-infoset table; report that
coverage metric N/A for this abstraction, rather than100%untrained or fullytrained.

`strategy.json.gz` is a frozen strategy artifact, NOT a resumable CFR R/S/RNG
training checkpoint: the reused C++ API exports strategy but not latent regrets.
Generation can be rerun from its fixed seed/config; no automatic resume exists.
Parent handles commits/push/new automaticCI. B ran no old QA or successfulCI again,
no production/DB/Storage/main/deploy/SSO/billing/destructive action.

## Independent native gate outcome (parent A)

Seven profiles x16384common worlds, seed17118102,13simultaneous intervals,
family99.9%. This exact B digest SB EV=-0.125336BB. Compared with frozen source,
pairedEV improves+3.374084BB [1.793749,4.954420]. Legal immediate-SB-fold deviation
has gain[-0.725361,-0.023967]BB: that SPECIFIC old weakness is resolved under this
confidence design. It does not prove full BR/NashConv improvement or GTO quality.

Fresh all169/action evaluation seed17118103 (25.302sec) still fails precision:
RFI root interval[-13.477397,13.051345]BB, width26.528742BB; maximum action interval
width100BB. vsopen root interval[-13.722134,12.817605]. Full nativeBR/NC upper and
training continuation/omitted-action error remain UNKNOWN. **Verified strategies0**;
no ordinary registration or search addition. Evidence: sibling
`../coverage-release-20261118/native.json` and annotated `B-all169.json.gz`.
No further B learning was run or scheduled after this precision failure.

A further independent native check gives a CONCRETE continuation blocker:
BB river-known-nuts valuejam, based only on own/public cards and exhaustive990
compatible opponent pairs, improves by0.314209BB;99.9% lower0.170583BB. Native
NashConv lower is therefore at least0.170583BB (point/upper stillUNKNOWN). B's
passive check/call continuation is refuted as a release shortcut. This does not
invalidate generation/legality, but it requires actual range-conditioned postflop
strategy before qualification. Evidence is in sibling B-native-deviation.json.

# PR120 safe recovery / public response boundary — 2026-11-17 JST

Starting HEAD: `1c21e98f513f0058a36fda06bbdaafe808111577`.
Read-only PR metadata: open, draft=true; remote git ref independently matches.
Eight PR workflow families completed SUCCESS (run IDs 43923224810,
43923224459, 43923224365, 43923224382, 43923224462, 43923224299,
43923224413, 43923224562). No manual rerun.

Fresh clone is clean at starting HEAD. Old session filesystem is not attached:
uncommitted work, unpushed commits, research DB, checkpoints and recovery ZIP
outside GitHub are UNAVAILABLE, not recovered. No destructive command used.
GitHub qualification, proposal and prior checkpoint/evidence files are accessible.

## Recorded criteria before implementation

Preserve all frozen policy/source/evidence bytes. Require exact public history,
acting-player cards only, all legal native sizes, explicit provider responses,
normalized finite nonnegative weights and errors on missing/illegal responses.
Check HU50 RFI/vsopen descendants and all169 classes; native legality on later
streets and short all-ins. These are interface criteria, not formal GTO PASS.

## Implementation and limits

`gto/qualification/public_response.py` adds immutable observations with exact public
ledger and legal action list, plus game/provider/implementation digest identity.
No nearest-size mapping, cursor alias or missing-row fold substitution. Incomplete
providers raise MissingResponse. It is deliberately separate from the frozen
Profile and does not change or silently repair prior counterexample policies.
Providers are not authenticated merely because callers supplied a digest; a later
qualified loader must verify artifact bytes and completeness before admission.
No default production provider, registry addition or search result is introduced.

The explicit call and uniform providers in tests are transport/legality fixtures,
NOT learned or qualified strategies. A complete strategic response generator is
still missing. This change is a prerequisite interface, not completion of B.

Six new tests: malformed weights/cards/terminal refusal; missing response refusal;
99 root actions / 98 nonterminal histories x169 hand classes (16,562 rows);
exact history distinction; 256 bounded native paths across two stack profiles,
all four streets and short all-ins. No hidden opponent cards enter the provider.
Existing10 qualification tests and immutable evidence checks preserved.

## Runtime / storage / stop conditions

Before build: 7.2GiB free; checkout265MiB. Budget: build/test <=5min,
new build <=50MiB, no training or population sweep. Measured build1.6MiB;
combined16 Python tests1.775s. Each test path capped below256 decisions;
256 paths fixed seed1201117. CI retains timeout-minutes5.
Local native binary is disposable; rebuild with pinned wheel, no auto-resume.
Source, commands and test log in Git are the durable restart point.

Commands:
```
python -B -m gto.qualification.build --directory /tmp/poker-public-response-build
QUALIFICATION_BUILD=/tmp/poker-public-response-build python -B -m unittest gto.qualification.test_qualification gto.qualification.test_public_response -v
python -B -m gto.release.verify_evidence
python -B -m gto.release.research_layout --check
node --test --test-isolation=none tests/gto-release.test.mjs
git diff --check
```
No TS/UI/package change: npm ci/build/lint and browser/mobile QA not repeated.

## Acceptance and next work

Formal12: 0/12 ->0/12. Requirements1 RFI,2 vsopen/3bet,3 vs3bet/4bet,
4 all169,5 EV,6 MTT/ring,7 players2–9,8 formal20stacks,9 positions,
10 ante/rake,11 formal sizes,12 search all remain non-PASS. The existing
acceptance-workgraph is unchanged. Eight candidates/1352rows remain
BLOCKED_UNVERIFIED; ordinary verified RFI0 / 3bet0. HU1BB stays separate.

Prior limited HU50 abstract frozen NashConv0.9321071527220774BB is unchanged;
no new NashConv, EV or BR measurement in this interface-only work. Full-native
BR upper, uniform continuation error and all169 EV precision remain UNKNOWN.
Prior counterexamples remain valid (RFI lower0.204084/0.311262BB; vsopen
conditional lower2.039733/2.117573BB), not complete BR upper bounds.

Specification evidence: existing spec-provenance.json identifies roadmap O06/Q05
and historical search, not a complete formal20-stack/size/rake table. A/B/C in
GTO_PREFLOP_RELEASE_PROPOSAL_20261117.md remain PENDING. Owner must decide
20 profiles/unequal stacks, chip grid/full sizes, ring rake/ante house rules,
minimum formal target and numerical quality thresholds. No decision inferred.
Independent of approval: use this interface to generate exact-history opponent
continuations for HU50 evaluation; first cover omitted3BB open and10BB3bet plus
SB re-response; then independent full BR upper / continuation error / all169
EV bounds for the SAME policy digest. Only after quality and condition approval
may certificate/registry/search be connected. No subset PASS counts as formalPASS.

Production DB/Storage/Vercel/main/SSO/fees untouched; Draft maintained.

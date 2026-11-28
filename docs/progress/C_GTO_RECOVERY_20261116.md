# PR120 recovery and verified-range boundary repair — 2026-11-16

## Acceptance recorded before implementation

Preserve Draft PR120 and branch codex/c-native-hand169-bridge-20261023.
Recover GitHub-confirmed source without replacing the frozen policies or existing
research data. Reject missing action/frequency/EV interval entries in both parser
and lookup. Preserve HU1BB and opt-in research; add no ordinary GTO datasets.
Formal checklist remains docs/qa/ev-precision-20261030/ACCEPTANCE.md (0/12;
10 PARTIAL and 2 BLOCKED), not reduced by this repair. Shared app files untouched.

## Recovery witnessed

Read-only PR metadata and git ls-remote agree on full starting HEAD
73f17fa13d0b7d611e228af7009aaf198d25ef89; no newer remote commit at recovery.
PR open, draft=true, merged=false. Its body still describes older 2d946fb and
must not be mistaken for current source/CI evidence. A full single-branch clone
into /workspace/poker-sns completed. git fsck --full exit0; initial status clean;
HEAD...origin left/right counts 0/0. Latest history: 73f17fa, e315127, 9a92f42,
2d946fb. No preexisting local checkout, uncommitted work or unpublished commits
were available in this fresh workspace. The recovery did not reset/clean anything.

All six latest-head workflow runs are SUCCESS, attempt1 (ci.json); none manually
rerun. Five are PR events, the sixth is push-triggered joint streaming. Artifacts
lists for all six runs were empty. No old recovery ZIP, checkpoint, policy SQLite
or training/cache DB bytes were found in the workspace or tracked repository.
The old reported 16.4MB ZIP and offline recovery cannot be reverified here.
GitHub source/QA recovery is successful; historical database recovery is NOT.

## Analysis reused, not recomputed population training

Rehashed 22 pure-BR evidence files and every source pin in provenance.json: PASS.
Rechecked frozen/full7 realization certificates with pure_br_report.check:
- frozen NashConv 0.9321071527220774 BB; recomputed max error
  4.9460435747050724e-14 BB (fsum arithmetic; distinct from recorded realization
  max 4.934941344458821e-14).
- full7 NashConv 3.113677782658094 BB; recomputed max error
  2.546851618490109e-12 BB.
- full7 minus frozen +2.1815706299360165 BB; no improvement/adoption.

Scope: restricted HU50, 169 private classes with compatible-combo chance,
1755 suit orbits/22100 flops, nine continuation branches; NOT full NLHE accuracy.
Largest signed full7 contribution: SB facing4bet after limp/raise2.5/3bet9/4bet21,
+2.051919847922753 BB. A9o/A8o/A7o are diagnostic private classes. BR-path gain
is not a one-row edit gain: do not sum these as independent local improvements.
Existing certificates integrate opponent cards before choosing shared preflop
responses; future boards cannot enter preflop action keys. Existing 10 pure-BR
regressions passed, including independent64-response comparison, shared keys,
clairvoyance rejection, read-only snapshots and retained regret/average history.
No new long training or checkpoint resume attempted without its original R/S.
No new mathematical update defect established. Frozen CF-vector code unchanged.

## Concrete repair

Array.some/reduce skip sparse holes. A reviewed synthetic dataset with a missing
action was incorrectly returned as verified; sparse probabilities summing to1
and missing EV interval endpoints were also unchecked. Materialize entries before
validation so undefined holes fail the existing type/finite tests. Regression
covers all four corruptions through validation and exact-query lookup.

Only src/gto/rangeCatalog.ts and tests/gto-range.test.mjs change behavior.
No certificate registration, UI strategy/preset, model, frozen engine or original
artifact modification. This is a data boundary fix, not new GTO precision.

## Local verification

- Regression before repair: 10 PASS/1 FAIL; missing-action record admitted.
- Node: node --test --test-isolation=none tests/gto-range.test.mjs
  tests/gto-abstract.test.mjs tests/gto-precision.test.mjs
  tests/gto-independent.test.mjs tests/gto-continuation.test.mjs — 26 PASS.
- python -B -m unittest discover -s tests -p test_pure_br.py -v — 10 PASS.
- npm ci --cache /workspace/npm-cache --ignore-scripts --no-audit --no-fund — exit0.
  Initial npm ci failed because default /home/agent/.npm cache was unwritable;
  lockfile/dependencies were not changed to fix the environment.
- npm run build — exit0; existing large-chunk warning.
- npm run lint — exit0; unrelated existing warnings, no new sparse-array warning.
- Existing gto-browser, gto-independent-browser, gto-continuation-browser scripts:
  21 PASS markers at390px, including all four histories and unsupported inputs;
  external page requests blocked, no page errors/overflow. System Chromium used
  via a temporary launch wrapper, no assertions changed. Initial local listen
  failed EPERM; network-enabled execution passed. Not authenticated production QA.
- git diff --check — exit0. Logs in docs/qa/recovery-20261116/.

## Remaining requirements / resume

RFI, vs-open/3bet, vs3bet/4bet and vs4bet research displays already exist, but
ordinary strategy admissions remain0. Search supports exact mode/position/stack/
size matching and separates dataset/policy/certificate identities. No new ordinary
ranges are available for MTT/ring,2–9,positions,ante/rake/formal20stacks/fullsizes.
Formal #1–7,#9–10,#12 FAIL to meet full requirement (repository PARTIAL);
#8,#11 UNKNOWN authoritative inputs (repository BLOCKED). PASS0/12.

Critical missing artifacts: original formal20-stack/full-sizing registry;
condition-matched authorized external reference/independent richer-game
calibration; historical R/S/cache/policy DBs for actual checkpoint continuation.
To unblock resume, make original checkpoint bytes available and verify identity,
read-only source hashes and resume parity on copies. Source manifests alone do
not reconstruct historical optimizer state. No paid access or deletion required.

Next precision experiment must preregister a tiny actual limp/raise/3bet/4bet/
shove game, genuine R/S teacher histories, fixed budgets and independent BR gates.
Existing eight-cohort nine-method experiment qualified no candidate. Do not
repeat it or full-population epochs blindly. Only a matched small improvement
justifies a new full trial; reserve2GiB and estimate storage/runtime beforehand.
Current fresh disk capacity is not the old session's reported1.11GB deficit.

Current work is finite and saved in Git; AUTO-RESUME:NO and independent scheduler:NO.
No main merge, Draft release, production DB/Storage/Vercel, protection, billing,
force-push, destructive Git cleanup or other development-line changes.

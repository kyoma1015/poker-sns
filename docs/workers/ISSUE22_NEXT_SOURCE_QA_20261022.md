# Issue22 next bounded manual source/QA invocation

Status: actual C source fix + A/B/D executed QA; not unattended development completion.

## Latest confirmed baseline

At16:43UTC PR108 head1b7dab0bcfc1ca642d4bf3cbb299c3b76a7ca20b /39813869671SUCCESS, PR109 head54f6b77a10c361f26798024f87d6e2ae770e9f0d /39814795806SUCCESS, PR38 head43cf45691555a34b0cb6163ba57cd699fd608005 /39815394081SUCCESS. All are unmerged Drafts with no submitted reviews observed. Later audit commits below supersede only documentation, not adoption.

## C actual new implementation

Task issue22-c-weighted-maximum-v1. Three identical finite EVs at +/-sys.float_info.max, weights1.0 or minimumsubnormal5e-324, raised intermediate fsum OverflowError despite a finite exact mean. Four independent Fraction oracles use the established exported float mass denominator. Immutable inputa78169a7a0731893ea1dd907a6a9c41eb933f0bd:62tests/4ERROR before→62PASS after; oldGTO40PASS.

Fresh complete openPR files/base/head snapshot, exact ancestor/blob overlap proofs, original4 state continuity, implemented dependencyC108, protected12file hashes and fixed baseline passed before lease/worktree creation. Formal agent /root/weighted_maximum_impl edited only gto/hand169.py. Host observed completion then independently verified fixedtest/sourcehash/tamper/noop/scope/commit. Source dd883b7ded3b792b366c12b18e3b1937ca469156 (+7/-1): only fsum intermediate OverflowError triggers exact fallback. Ordinary fastpath and previous source fixes retained, no clamp/blanket exception suppression.

Draft110 https://github.com/kyoma1015/poker-sns/pull/110 ; head5d4d031f472e9c0e1631ef0d532295ec44b10d20 adds separate boundedcontents:read CI. Run39817184387 completedSUCCESS. Depends on latest C108/105 source, not a main merge candidate; do not double-merge stacked old branches. No G11 compatibility/real strategy convergence claim.

## A/B/D QA actually executed

- A109 CLI6PASS: deeply nestedJSON,5000digitinteger, invalidUTF8, null, booleanlane all fixed sanitized rejection; normalJapanese complete nonexecutableJSON. Reusable temp-only A-cli-qa.py and log stored with evidence.
- B PR98: data27PASS, savedanswers14PASS. One browser subtest fails its runner because managed spawnSync node EPERM: environmentBLOCKED, not a successful browser QA or proven source defect. Same permission probe not repeated.
- D PR100: audit5PASS/core53PASS.
- Additional independent B4/D4=8PASS: frozen input nonmutation, sparse filters, normalized duplicate review-only, single-call transport; all50invalid answerpositions,3nonfinite scorecases,36asset omissions. No new sourceFAIL, official350 accuracy/D36expert semantic validity remain unverified.

QA scripts/logs are exact manual artifacts in docs/qa/issue22-next-source-qa-20261022/. The B/D harness imports two pinned retained worktrees by absolute path: B8b1e0cf79160135bf69711abe69a2dffb8701a09 and Dd89347092cfeb22b4ab8bc88e042f502df9d7798, Nodev24.19.0. It is NOT a portable mainCI task; restore those exact source checkouts before repeating. A CLI script accepts a pinned checkout root. No dependencies were installed. No browser success or TDA/animal domain proof is implied.

## State/hash limits and scheduled probe

Existing original40 statuses and oldBLOCKED rows preserved. New total43:41implemented/2blocked/running0. Retained public candidate/manifest canonical hashes match41/43, including38/40original and original4anchor. Two old selective-integration descriptors (A-main-controller-transplant/C-main-gto-transplant) could not be independently reconstructed: UNKNOWN, not a claimed all40hashPASS. No state replacement, expiredlease theft or live controller/schema adoption.

The existing second probe is configured for2026-10-22T17:02:46UTC (Oct23 02:02:46JST). At the latest lookup it was future. First observed prompt/last_run_time16:03:40.474110, but last_run.id/start/end/chat_ref/latest_result remain null. next_run_time null causeUNKNOWN; no independent coldstart claim. **The existing probe is READ ONLY: it must not acquire leases, start source workers or write state. Those operations cannot be proven by this probe without changing its authorized scope.** This manual source implementation is separate evidence. Original6h remains paused, no reservations registered/changed/extended.

Checkpoint advances are intentional authorized manual work. Next observation must read current checkpoint and immutable source/CI evidence, not mistake a traced digest/count change for automatic implementation or corruption. Source is saved before end; formal source worker now complete, not a persistent daemon.

## Next allowed action / approval boundary

Observe existing second readonly run without modifying its scope. Read current CI/PR/source/checkpoint before choosing any new task; never replay completedC110/C108/A109. Recover two old integration descriptors for independent hash verification. B original350/RPC evidence, D expert labels and G11/actualstrategy convergence remain domain gates; no invented tests or publication.

Finite development operation PROPOSAL ONLY: hourly2occurrences, max30min each/60min total, concurrency1, zero newcharges, stop on unknownstate/auth/quota/liveness/overlap. A reviewed common controller+checkpoint+guard SHA and independent backend/runID evidence must be established before asking for activation approval; PR106/107 are unmerged component artifacts, not a deployed combined controller. No new scheduler/controller switch authorized here. Main merge/productionDB/Vercel/billing/pollrelease remain prohibited.

# Issue22 main-based selective integration — 2026-10-22

This supersedes the previous recommendation to prepare main-based candidates: candidates are now implemented, tested and published independently. No existing Draft branch was merged; source code was reused with exact-byte provenance. No poll SQL/UI/notifications or PR72 edits. No production DB, Vercel, billing or main merge.

## Fresh main and scope
Initial main: `7da31f078624178dbddf8f1edf59eb8d0bf782b7` (external PR71). Unlike inherited progress prose, actual tree contains neither `scripts/code_worker.py` nor GTO subtree. Thus an initializer-only patch cannot apply to main. The minimal controller dependency/test closure is explicitly imported, not silently treated as already integrated.

During work main independently advanced to `d8b3687f058227ce8a779d463262d4e2b6fad536` (external PR72), only adding `docs/qa/issue22-poll-production-release-runbook-20261022.md`. Original fixed input remains immutable; fresh comparison against updated main is recorded. This worker did not perform that merge or alter its runbook.

## A: controller candidate
Draft74: https://github.com/kyoma1015/poker-sns/pull/74
Branch `codex/a-controller-main-input-20261022`; source head `2a1f39264f2b467df652a33864de659f6537e92e`. Exact10 reviewed modules/config/tests from PR69 `4d30c7ac0d08104f9d159987e38c823ef7c3b419`, plus dedicated isolated CI, provenance/evidence and two meaningful timeout/restart tests. Controller code hash `37a539e207c46ee5ad94bdf6c877cf835e5188a217169ed1f5aa2885ce0def15` unchanged. No queue/worker activation; config remains validation-only.

PASS: protected27, existingworker22, queue15, timeout/restart2. CI39723091434 SUCCESS at exact head. Existing main poll-release regression CI runs separately; do not equate controller-specific success with all required release gates.

Lock audit: bounded setup guard precedes connection, WAL and schema creation. Initialization releases it before lease transaction; claim commits before subsequent Git preparation lock. Initialization exception closes connection then releases guard. Existing30second setup deadline and10second SQLite busy timeout retained. Four-worker fixtures/eight-initializer test and process exclusion pass; external noncooperating SQLite clients may still cause bounded failure. Crash/restart test proves OS guard release, not arbitrary database recovery after corruption. Live retained controller not replaced.

## C: minimum GTO validation closure

Draft75: https://github.com/kyoma1015/poker-sns/pull/75
Branch `codex/c-gto-main-transplant-20261022`; head `b7f3d2910526c8762ac4b19acb2e8fee7535d8a9`. Local40+29+5PASS and freshly compiled17settlement+16rank7 comparisons PASS. DedicatedCI39723383344 SUCCESS.

C candidate imports only preserved GTO regression/fixture/reference code, not old SNS/security branches. `gto/native/settlement.py` must equal PR66 bytes, SHA256 `e8e31465465b0645c3b2e7f9e49f23b1e37b0963853c20bbf840dc3c63cfdece`. Fixed C acceptance stays byte-identical but in `gto/integration_acceptance`, preventing tests from absorbing A lane tests.

Minimum purposes: settlement+rank7 fixtures/bridge for Python-C++ comparison; hand169/checkpoints and four existing test files for unchanged40 regressions; five immutable fixed tests for29 acceptance; compressed Python reference/header for verified reference; three compressed solver payloads+verifier solely for source hash audit, not a solver rebuild. No original backend/checkpoint/vendored binary copied.

New install-free launcher bounds/strictly decodes original10318-byte Python reference and10159-byte Ledger header, checks known hashes, checks pinned public pybind11 wheel SHA before extracting headers only, compiles a test bridge in owned temporary storage. No pip install or Abseil required for this bridge. Dedicated read-only CI; no model keys/networked runtime activation.

## Unresolved evidence
B350 snapshot/original Longform hash/ID-by-ID review: BLOCKED; D36 authoritative classification definitions/expert animal labels: BLOCKED. Rechecked handoff tree latest `ae22acd1ba5d167f1d7111069966dda672260129`,171 entries,truncated=false; absence is scoped, not proof of global nonexistence. Sender reports and hash ledgers are not receipt of original bytes. No unverified TDA publication or semantic-validity claim.

G11 original vendor closure/ABI/config/baseline/full historical checkpoint: BLOCKED. Synthetic960 cases,33 reference comparisons and toy NashConv do not establish original compatibility or full poker convergence. Positive_live/dead-ante rule edge remains unresolved. Existing PR66/69/70 and originals retained.

## Integration execution boundary
These are explicit-user-authorized selective integration tasks under new A/C integration leases and formal collaboration, not replay of completed original task IDs or a scheduled model run. Root retains the existing shared state, verifies original4 specification hashes/status, and records only sanitized integration results. No private lease token/receipt/SQLite/credential/backup is published. No worker prepare/finish receipt cycle or resident daemon is claimed for this selective-import workflow. Completed integration leases do not activate either candidate on live controller/main.

Next: review independent candidates and current mergeability/CI before requesting explicit main approval. Controller adoption, any main merge and poll release remain separate decisions. Original evidence gaps require actual source/reference/expert artifacts, not synthetic PASS substitution.

## Publication drift and overlap review
Latest observed main subsequently advanced to `5a49f437727fba0f4d48585300a04ec7e9d747a4` (external PR73, adding only backup-feasibility documentation). Both candidates return exit0 from non-destructive merge-tree against this exact main. No index/worktree/ref merge performed. Fresh44-open-PR base/head/full-file snapshot includes new other-owner PR76/77 (poll threat-model doc/PG17 synthetic restore workflow); no path overlap with A74/C75. Do not edit or duplicate those tasks. A74 and C75 changed-path sets are disjoint.

Existing source ancestry/reuse: A26/34/38 primitives → reviewed69 → selective74; C25/33/57/61/66 GTO validation → selective75. These are reviewed reuse routes, not authority to independently merge every ancestor. Exact imported bytes are verified against source repository objects. Existing Drafts remain open/unmodified in code. PR70 toy metric intentionally excluded from minimum PR66 closure. Unknown or moved future heads still require fresh review; this manual integration review does not weaken autonomous planner gates.

GitHub Vercel commit statuses on both new heads are FAILURE: “Deployment rate limited — retry in24hours.” No Vercel API/CLI, deployment retry or bypass was attempted. GitHub Actions success is recorded separately from this external status and production release approval.

## Final observed CI and gate ledger

| Gate | Result | Evidence |
| --- | --- | --- |
| A selective import/isolated tests | PASS | Draft74, CI39723091434 SUCCESS |
| A existing app/build/lint/mock-browser/isolated-DB CI | PASS | CI39723091294 SUCCESS; no production QA claim |
| C exact21 source import/40+29+5/native17+16 | PASS | Draft75, CI39723383344 SUCCESS |
| C existing app/build/lint/mock-browser/isolated-DB CI | PASS | CI39723383251 SUCCESS; no production QA claim |
| Both candidates vs observedmain5a49f43 | PASS | merge-tree exit0 each, no branch integration |
| Sharedstate/original4/newintegrationleases | PASS | original4 hashes/status preserved; newA/C implemented; running0 |
| B immutable350/original-source/clause evidence | BLOCKED | handoff tree/workspace bounded recheck, no new originals |
| D36 semantic validation | BLOCKED | no authoritative expert animal labels |
| OriginalG11 ABI/checkpoint and actual strategic convergence | BLOCKED | missing originals/independent game-specific acceptance |
| Vercel commit status | FAIL (external) | rate limited; no retry or bypass |
| Main merge/live adoption/poll production release | BLOCKED | explicit review/approval and release gates remain |

Overall CONDITIONAL PASS: safe main-based candidates and isolated tests complete; no main integration/live activation/release. Exact commands and byte manifests are stored in each candidate, CI/head/state/PR snapshots in docs/qa/issue22-main-transplant-20261022/.

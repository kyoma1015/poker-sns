# B TDA isolated release candidate — 2026-10-20 JST
Status: CONDITIONAL PASS; NOT released.
Base main: f8890b6ec11d30676c55dc7dc8801f1da8549d28.
Branch: codex/b-tda-rpc-isolated-release-20261020.

This is the independent main-based slice of development PR #14, not a merge of PR #13. Only TDA client/data helper, offline audit CLI, regression/browser fixtures, pinned playwright-core dev dependency, narrow CI and evidence are included. No other unmerged SNS/F03/diagnosis/GTO source is imported.
The only semantic reconciliation was the first import: include tdaQuizData, retain main's existing inline authentication function, and do not accidentally import PR11's unmerged auth helper. This candidate does not fix main's separate auth-network-vs-expiry issue; that remains PR #11 work.

Acceptance: reject malformed question options before rendering; release spinner after thrown fetch/save failures; retain saved correctness/score if optional explanation fails; no blind write retry; offline audit always marks official correctness UNVERIFIED and publication false.
Implemented: strict question/option structure validation (including duplicate IDs/orders), copy-sorted option order, caught filter/normal/hard/wrong/answer/detail RPC transport exceptions, offline count and normalized duplicate-candidate audit.
No correct answer/content/scoring, SQL or permissions changed.

Verification on this main-based source:
- npm ci --cache /workspace/work/npm-cache --fetch-retries=0 --fetch-timeout=15000: PASS.
- node tests/tda-quiz-data.test.mjs:17 PASS.
- npm run build:PASS (large chunk warning).
- npm run lint:PASS (46 pre-existing warnings, zero errors).
- node tests/browser/tda-quiz.mjs:5 PASS on Chromium154.0.8037.57 at390x844. Real TSX, synthetic questions, in-memory transport, external HTTP blocked. All three fetch modes recover, malformed options do not render, saved answer survives explanation outage with one submit RPC.
Logs are committed in this directory. CI repeats all gates on this branch.

Release gates:
- No main merge, deployment, production authentication/DB/SQL operation, user-data changes or question publication performed.
- The published350 corpus and official TDA reference bundle were not received. Counts/semantic correctness/逐条 coverage remain UNKNOWN. CLI does not approve publication.
- No proven isolated DB/real-auth integration test environment exists here. Actual RPC/auth behavior remains a separate gate.
- Existing main production dependency high vulnerabilities are not repaired by this TDA slice; apply and verify the independent security fix before release.
- Production deployment authorization/access is assessed by the coordinator. Do not infer readiness from this UI-only test suite.

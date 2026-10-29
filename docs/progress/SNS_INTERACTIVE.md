# SNS | Poll-only integration candidate
Date: 2026-10-20 JST
Status: CONDITIONAL PASS for development; production release BLOCKED.

Binding scope: docs/handoff/POLL_ONLY_SCOPE_CORRECTION_20261020.md on handoff branch (8509484bf9186534ca10694eb62aba7075395aee).
Question boxes are excluded. Both home and bottom-nav composers offer polls only. Both creation entry points call createPollRequest, which rejects stale question mode before RPC and validates 2–4 nonempty unique options, content, allowed deadlines and privacy mode.
Historical question SQL, data and internal QuestionThread code are retained. The public card never mounts QuestionThread; timeline/reposts exclude known question posts and detail links display unavailable. This is a UI restriction, not a new DB access policy; old clients and direct RPC access require a separate server review.
Anonymous result presentation strips voters/answers without mutating the source response. Named voter lists remain available. Client redaction is defense in depth, not proof of RPC/RLS confidentiality.

Tests: node tests/interactive-requests.test.mjs (10), node tests/poll-only.test.mjs (17), mocked browser coverage for home and bottom-nav composers, named/anonymous display and question card exclusion. Full integrated evidence is recorded in docs/progress/INTEGRATION_VERIFICATION_20261020.md.
No SQL executed or modified. Four SQL files are historical references and cannot reconstruct the complete v4 runtime schema.
BLOCKED: no isolated DB; server-side three-actor anonymity, direct notification INSERT permissions, one-vote enforcement, deadlines and exactly-once close notification/cron need isolated DB integration tests before production release. Browser tests with an in-memory transport do not replace those tests.
PR #4 is superseded by corrected PR #12 and the integrated Draft PR. Question-box QA is out of release scope.

## Issue22 poll independent candidate: isolated acceptance complete 2026-10-21
PR31, tested b90bd5f34c3791e4ad5da762c51f972a8d73710d, CI39572765844 SUCCESS: real official Supabase Postgres/PostgREST56PASS plus client30/build/lint/audit/mobile mock5. Three-actor anonymity/RLS, legacy RPC, notification privilege preservation/forgery, actual cron, concurrent retries, rollback and retained historical data passed. Exact JSON: docs/qa/issue22-polls-20261020/database-results-ci39572765844.json. Production BLOCKED: schema parity/SQL approval/migration history+advisors/full real-DB UI QA/deployment access. GoTrue absent; this is not production login testing. Question creation remains disabled; old data kept.



## Backup-only JIT/read-only connection correction (2026-10-30 JST)
Dedicated branch: codex/backup-jit-readonly-options-20261030; based on main 73f2a4398ae20ca14d6ad89000bba13a7b4ad18b.
Acceptance: reproduce libpq URI options overriding PGOPTIONS, then show JIT + default/current read-only + TLS together, actual INSERT/DELETE rejection despite synthetic grants, successful pg_dump/pg_dumpall, retained source row, and no credential output.
Implementation: validate the stored URL, require the approved backup role and postgres database, decode into an exclusive 0600 libpq env file under a private directory, combine JIT/read-only startup options once, and pass only that file into the PG17 client container. No secret URL in process arguments, no extra connection-string expansion, no production credential changes. Raw database client diagnostics stay in private temporary scratch and are never published. All plaintext connection settings are removed on success or EXIT.
Local acceptance: 20 preflight tests and shell syntax PASS. CI includes the new disposable TLS PostgreSQL regression; its actual result is recorded in the PR/checks, not presumed here. This is not a live Supabase JIT or production backup/restore result. No JIT grant, manual backup dispatch, main merge, production DB change, Vercel change or PR #123 change is authorized by this code. Owner approval is required for main merge; renew the explicit JIT expiry only after integration.


## Direct-backup IPv6 diagnosis (2026-10-30 JST)
Branch: codex/backup-direct-ipv6-probe-20261030. Acceptance: measure the actual ubuntu-latest runner IPv6 default route, production direct-host AAAA resolution and one bounded TCP/SSLRequest + hostname-verified TLS handshake, without credentials, authentication, queries, tunnels, paid IPv4 add-ons or network changes. Dedicated PR-only workflow has contents:read and no protected environment/secrets. Local syntax and credential-free workflow checks PASS. Real runner result is recorded in PR/checks; do not interpret workflow existence as reachability or backup success. Existing JIT cutoff 04:30 JST has passed: no JIT connection or grant renewal is authorized by this diagnosis. Production backup Run 40935009252 must not be retried for the known pooler JIT provider error. Main integration, Secret changes and a new exact JIT expiry require explicit approval. PR #123 and production build-stop remain untouched.

Actual ubuntu-latest diagnosis: commit 11ad6ff182a529f6bc06532faca85146e2992e4e, Run 40941230038, DNS AAAA=1, IPv6 default route=false, TCP=false, errno ENETUNREACH; auth=false, credentials=false, SQL=false. Direct path is BLOCKED on that runner. Follow-up checks the distinct standard ubuntu-24.04-arm runner once; GitHub docs list it as free for public repositories. No production JIT retry, tunnel, Secret mutation or paid service.

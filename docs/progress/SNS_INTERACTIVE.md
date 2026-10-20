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

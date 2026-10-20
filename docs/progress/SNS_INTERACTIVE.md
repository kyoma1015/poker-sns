# SNS | Poll/question-box isolated candidate
Date: 2026-10-20 JST
Status: CONDITIONAL PASS; release and live preview QA BLOCKED.

Base main: f8890b6ec11d30676c55dc7dc8801f1da8549d28.
Historical candidate: fa90c3320094d8def6e0e4a1248171837f1ba366 / draft PR #4.
Ported candidate UI and four historical SQL reference files into a separate main-based review branch. SQL files are historical references, NOT an instruction to apply migrations.
Fixed poll request privacy mode (previously always true even for named polls), and revalidate option/deadline at click time so an open card cannot submit a stale expired vote.
Tests: node tests/interactive-requests.test.mjs: 10 PASS for named/anonymous requests, invalid choices, exact deadline, missing deadline and wrong post kind. These do not prove server-side anonymity/RLS.
Dependency install/build/lint blocked locally by unavailable registry proxy; PR CI provides isolated build.
Live preview writes and production/shared Supabase tests were not performed. No isolated DB configured; SQL/RPC/RLS/cron behavior remains BLOCKED. v4 creation, v2 response, v4 read and question-thread RPCs are runtime dependencies; four legacy SQL files alone are not complete reconstruction.
Do not apply these SQL files or re-run existing production migrations. Current application history UNKNOWN in this run; earlier migration observations must be checked separately.
Remaining: isolated schema/three-actor anonymity tests, question-thread ownership/edit/delete tests, poll-close cron, and preview QA against a proven isolated DB. A/SNS share Timeline/PostDetail and require semantic integration rather than whole-file replacement.


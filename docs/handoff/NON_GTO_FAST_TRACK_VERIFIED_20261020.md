# Poker ID non-GTO fast-track: verified GitHub state (2026-10-20)

## Directly verified GitHub PR status
- #1 merged — amusement -> ring game naming.
- #2 open/draft — Poker ID card WIP. **Do not infer feature absent from main**; #3 separately merged card release.
- #3 merged — Poker ID Card release PR. **Merge is not Vercel production evidence.**
- #4 open/draft — timeline polls/question box; mergeable=true at query time.
- #5 open/draft — player-type audit phase1; mergeable=true at query time.
- #6 merged — TDA unauthenticated login guidance.
- #7 merged — TDA login button dark styling.
- #8 open/draft — development coordination/CI; mergeable=true at query time.

## Verified compare against main (GitHub API)
| Branch | Ahead | Behind | Main-impact files |
|---|---:|---:|---|
| fix/p0-security-audit-20261018 | 89 | 2 | 20 (includes src/App.tsx, src/Notifications.tsx, SQL, OG APIs) |
| fix/player-type-audit-phase1-20261019 | 2 | 2 | src/PlayerTypeDiagnosis.tsx |
| fix/player-type-qa-phase1-20261019 | 3 | 2 | src/PlayerTypeDiagnosis.tsx, src/playerTypePresentation.ts, src/playerTypeQuestions.ts, tests |
| feature/timeline-polls-questions-20261017 | 48 | 2 | 8 (timeline SQL, Notifications, PostDetail, Timeline, TimelineInteractive) |
| fix/tda-quiz-login-guidance-20261019 | 2 | 2 | src/TDA.tsx |
| fix/tda-login-button-dark-20261019 | 1 | 1 | src/TDA.tsx |

Counts are compare API snapshots, not proof of functional QA or deployment.

## Parallel execution plan (no owner approval needed for read-only/isolated work)
1. A security lane: read-only inspect F03 RPC/permissions/notification flow and integration patches; write failing reproducible test first. Do not integrate 89-commit branch wholesale.
2. D lane: compare two player-type branches, enumerate distinct fixes and tests, prepare clean integration branch and run tests. No SQL production writes.
3. B lane: verify main includes merged #6/#7 and run TDA tests, inspect current published question validation; do not claim official question correctness from counts alone.
4. Cross-product lane: compare PR #4 to main, review SQL migration and notification/permissions dependencies, run isolated build/tests and report release blockers.
5. Release lane: read Vercel deployment commit, production DB migration state, and browser QA evidence; no production writes. Keep UNKNOWN if access unavailable.

## Release gate
PASS requires exact commit, isolated tests, security/DB impact analysis, browser QA as applicable, and verified deployment status. Do not merge main, deploy production, or modify Supabase without explicit owner authorization.

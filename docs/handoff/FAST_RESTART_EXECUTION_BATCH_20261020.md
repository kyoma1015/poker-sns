# Poker ID — fast restart execution batch (2026-10-20)

## Read-only findings
- F03 selective integration plan at `docs/audits/F03_selective_integration_plan_20261020.md` on `fix/p0-security-audit-20261018`, blob `1dfa37e7471cd5ff8adabdd6c20b3a134e4fcbfc`. It explicitly specifies exactly five files: `src/createVerifiedNotification.ts`, `src/Timeline.tsx`, `src/PostDetail.tsx`, `src/PlayerProfile.tsx`, `src/App.tsx`. Direct notification INSERT remains allowed for old clients; do not revoke before transition and separate approval. Do not overwrite full TSX files.
- F03 phase 2 SQL `sql/f03_phase2_legacy_comment_cutoff.sql` on audit branch, blob `ad4ee0c308f845a4966efa10467a3f8334750cd7`. Its header *claims* applied to Supabase 2026-10-19; this claim is not an independent live DB check. Function validates like/comment/follow event provenance and uses SECURITY DEFINER; old direct INSERT remains unresolved.
- D QA branch `fix/player-type-qa-phase1-20261019`: `src/PlayerTypeDiagnosis.tsx` blob `aaa654dca6dbbdbc2f9312f9fa441902ccbbe076` includes request invalidation, retry and deep-link guards. `tests/player-type.test.mjs` blob `301486a158fe56a31c22b46d36c165cbcd8f01bc` includes 50-question integrity, trait normalization, persona fixtures, request gate tests. These are **test source observations**, not evidence that tests have run in Codex.

## One-batch execution order for Codex
1. Fetch current `main` and each target branch HEAD and log immutable SHAs; read `AGENTS.md` and current QA docs.
2. F03: apply **only** selective 5-file integration on a new non-main branch; first establish expected failing tests; preserve unrelated main features; run `npm ci`, build, lint, unit tests; test direct INSERT protections in isolated/test DB only. If DB unavailable, mark blocked.
3. D: diff both diagnosis branches; port distinct fixes to another clean branch based on current main; run `tests/player-type.test.mjs` and build/lint; document L01 DB migration as unknown until read-only evidence.
4. B: inspect main after merged #6/#7; run available TDA tests; independently check published question correctness where source and official text available.
5. SNS: inspect PR #4 and SQL, test isolated preview; do not touch production.
6. Return one matrix per lane: branch SHA, files changed, tests commands/results, SQL/production unknowns, blockers, draft PR URL, and smallest release decision needed.

## Hard stop
No main merge, production deployment, live Supabase writes, third-party user interactions, or expense without explicit owner approval. Draft PRs on isolated branches are allowed. A handoff doc or test source does not count as completed implementation or passing QA.

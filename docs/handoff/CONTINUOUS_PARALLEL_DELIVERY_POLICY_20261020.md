# Owner-approved development operating policy — 2026-10-20

## Workstreams
1. **SNS / ordinary development:** continue feature development, UX fixes and bug fixes.
2. **TDA quiz:** continue content QA and functional improvements; maintain verified-only publication requirements.
3. **Player-type diagnosis:** continue 50-question / 36-animal accuracy, UI and real browser QA.
4. **GTO:** separate ongoing development track; do not block the other three on native build/checkpoint restoration.

## Delivery cadence
- Work in parallel, separate feature branches and PRs, batch related changes, and use CI to reduce user round trips.
- Ship small, independently verified features to production progressively, rather than waiting for GTO.
- Owner wants rapid releases with minimal back-and-forth. Treat this as a general direction, **not as permission to bypass release gates**.
- Production merge/deployment may proceed only after required checks pass and the relevant deployment environment, access and approval boundaries are satisfied. No speculative claims of automatic continuous execution. Never run production SQL without reviewing migrations, backup/rollback and privacy/security checks.
- PR #13 remains Draft until notification authorization/legacy permissions, poll anonymity/RLS/close notifications, production dependency vulnerabilities and required QA are addressed. Do not merge it wholesale to expedite other unrelated features.
- Question boxes are **not** a release feature; polls only. Preserve historical data.

## Codex execution plan
- Run 3 non-GTO lanes concurrently, each picking safe, independent backlog items from docs/progress/MASTER.md and relevant progress docs. Complete implementation, regression tests, build, lint, PR, and release evidence. Rebase or cherry-pick with semantic conflict resolution; no duplicate merging of PRs #9–#13.
- Run GTO in its own lane. First restore vendor bundle/G11 references/checkpoint; prove C++ build, reproducibility and checkpoint compatibility before claiming solver readiness.
- Track each PR with release gate: CI, browser QA when relevant, isolated DB/RLS/privacy verification when relevant, dependency audit and rollback plan. If a gate is blocked, continue other independent work and leave that PR unmerged.
- Report only actionable blockers and actual releases with commit SHA, PR, production deploy evidence, and QA result.

## Scope note
This document records the user's direction. It does not start background Codex tasks or itself authorize risky production database operations.

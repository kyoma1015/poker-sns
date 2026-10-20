# Poker ID: binding product scope correction — polls only (2026-10-20)

## Owner decision (2026-10-17; supersedes older poll/question-box plans)
- **Ship polls (アンケート)**. Named/anonymous voting, 2–4 options, voter list as privacy permits, results, one owner notification at close.
- **Do not ship question boxes (質問箱)**. Hide new-question creation UI and exclude question box from release. Preserve historical question data, existing internal code and DB; do not delete/migrate away historical rows.
- Old PR #4 and new Draft PR #12 must be evaluated against this latest decision, not old descriptions.

## Direct GitHub PR #12 patch inspection
- `src/Timeline.tsx` has `(['poll'] as const)` for composer buttons, but still maintains `interactiveMode: 'normal'|'poll'|'question'` and a question composer path.
- `src/TimelineInteractive.tsx` still has `QuestionThread` and renders it for `kind==='question'`. Internal historical support can remain, but exposure must be explicitly reviewed.
- `sql/timeline_interactive_posts.sql` supports `kind='question'`; historical SQL is not to be re-applied or modified in production as part of this scope correction.
- `tests/interactive-requests.test.mjs` tests poll voting and rejects question-kind via poll write contract; it does NOT prove question-box UI is hidden.

## Mandatory acceptance tests before PR #12 release
1. Home composer and bottom-nav post composer show exactly one interactive creation action: アンケート. No 質問箱 button or navigable new-question form.
2. No UI path can submit `p_kind='question'` for a new post. Explicitly guard creation path against stale question mode, not only hide the button.
3. Historical question data remains intact. Preserve internal code/DB; do not claim historical question UI visibility is approved without owner decision.
4. Named polls show names/votes only under named mode; anonymous polls never expose voter identities, including RPC, RLS, notifications and history.
5. Poll options 2–4, deadlines, results, voter list and exactly-once close notification tested against isolated DB and browser QA.
6. Change docs/progress/SNS_INTERACTIVE.md and PR title/description to 'poll-only' scope. Mark question-box QA out of release scope. Avoid SQL execution.

## Gate
PR #12 is **NOT READY** for production integration until tests 1–2 and privacy validation pass. No main merge or production DB changes without approval.

# B — usable quiz completion after uncertain saves

Status: CONDITIONAL PASS (client flow); official question truth and actual DB/auth remain BLOCKED.
Start: `245d55bae1f03073dc519e5c307bc1fc4b96138b`, existing PR119 descendant branch `codex/b-snapshot-integrity-audit-20261023`. No new PR/SQL/RPC/schema/question changes.

## Product acceptance recorded before repair

An answer RPC can have committed even when its response is lost. A user must not be invited to write the same answer again merely because the result was not observed. The user must still be able to continue the quiz, without classifying an unknown answer as correct or incorrect. A known successful save must remain usable even if optional explanation retrieval never finishes. Late enrichment must not replace a later question's answer. Explicit permission rejection retains login guidance. These complete one client save/recovery/navigation flow; they do not provide database idempotency or official-answer correctness.

## Changes

- `src/TDA.tsx`: preserve selected option and prevent another submit on ambiguous failure; explicit unscored next/finish; separate confirmed-answer denominator and original question numbers; no invented score for zero confirmed answers; display structurally valid save immediately, before optional read-only detail; generation guards across start/auth/question/save/detail/next/reset/unmount.
- `tests/browser/tda-save-recovery.mjs`: seven actual React/Chromium scenarios at390×844, all remote requests aborted, synthetic question/user/transport only.
- `tests/browser/tda-supabase.ts`: own synthetic uncertainty/delayed-detail fixtures; original six browser scenarios retained.
- `tests/tda-save-recovery.test.mjs`: bounded browser wrapper plus three actual locked Supabase SDK/injected-fetch tests. No network/DB request reaches a real service.

## Fixed evidence

First fixed phase5cases:1PASS/4FAIL→5PASS. Related optional-detail case:6cases5PASS/1FAIL→6PASS. Final identical seven inputs:1PASS/6FAIL on pristine start SHA in a separate detached temporary worktree →7PASS on repaired source; see `final-input-before.log`, `fixed-final.log` and `legacy-browser.log`.

The SDK documentation search suggested retries could include POST, but the installed locked `@supabase/postgrest-js` source limits retries to GET/HEAD/OPTIONS. The actual SDK tests confirm HTTP503, network rejection, and permission rejection each send exactly one POST. No unnecessary retry helper/global-client change was made. This distinction is preserved rather than claiming a nonexistent SDK bug.
Docs consulted (documentation only): https://supabase.com/docs/guides/api/automatic-retries-in-supabase-js . The installed source/observed behavior takes precedence for this pinned version.

## Commands

- `npm ci --cache /tmp/poker-b-npm-20261025` (single successful retry after default npm cache could not be created; no HOME/auth relocation)
- `node tests/browser/tda-save-recovery.mjs` (same source inputs in original/repaired checkout)
- `node tests/browser/tda-quiz.mjs` (six preserved synthetic-browser cases)
- `node tests/tda-save-recovery.test.mjs`
- all `tests/*.test.mjs` individually (bounded subprocesses; regression.json records counts/status)
- `npm run build` (TypeScript+Vite), `npm run lint`

## Local results

277 root tests PASS/0FAIL (273 preserved+4 new root tests, including seven mobile cases and three installed-SDK tests); existing six mobile quiz cases separately PASS. The source SHA256 and per-file counts are in regression.json. Locked install, TypeScript/Vite build, and lint PASS; existing lint warnings and large-chunk warning retained. The final source-generation review was followed by relevant tests and a full immutable-source regression rerun.

## Remaining gates

Real server idempotency, multi-tab/server retries, auth/RLS and runtime integration require reviewed isolated DB evidence. No production connection was made. Auth account-switch clearing is not established by these cases. No timeout/cancellation guarantee for an optional request itself is claimed; the confirmed-save UI no longer waits for it. Official350 immutable export/key/original-language rules/authorized translation/per-clause review are absent and remain BLOCKED. All synthetic material is explicitly synthetic. No content publication is approved.

Existing PR119 is still the intended Draft; the parent publisher must verify exact head and automatic CI after saving this tested tree. Local PASS is not CI/integration/release proof.

## Same-tick activation continuation

The actual React mobile harness invoked the same option DOM button twice in one JS task, before React rendered the loading state. The preserved final seven cases passed, but the eighth produced two submit RPC calls (7PASS/1FAIL; double-before.log). A synchronous per-question-generation claim now prevents this second write before the first await. Auth failures before dispatch and explicit permission rejection release the claim; confirmed and uncertain writes retain it until the next question/new run. No server-side idempotency guarantee is claimed. Final eight mobile cases pass via the four root tests (browser wrapper+three real-SDK cases). The preserved six browser cases and28 quiz/filter cases were rerun, followed by build/lint (double-final-* logs). The277 full-suite snapshot above belongs to the prior source hash recorded in regression.json; this narrow continuation has targeted reruns and awaits exact-head CI for the full final source.

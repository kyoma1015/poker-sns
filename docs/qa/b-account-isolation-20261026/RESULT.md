# B — account-scoped quiz lifecycle

Status: CONDITIONAL PASS. Client identity isolation implemented and locally verified; real authentication/RLS and official350 correctness are separate unfinished gates.

Start/source ancestor: published PR119 head `5416f6c283bf723d551b069fca9a6215b80b562c`.
Local branch: `codex/b-account-isolation-local-20261026` (no child GitHub writes).

## Acceptance fixed before implementation

Changing/signing out the account must clear questions, selected answer, score and local review history. A response belonging to an earlier identity must not restore them. An auth event must invalidate old handlers synchronously, before React commits its new render, so an old option handler cannot write for a new account. Fresh verified identity must match the pinned quiz identity even if a subscription event was missed. Same-identity token renewal must preserve an in-flight quiz. Auth callbacks must be synchronous, make no SDK calls, and unsubscribe.

Nine real React/Chromium390×844 cases use a synthetic in-memory transport. Every external request is aborted. No real Supabase client, user, credentials or DB is used by these browser cases.

Fixed before:1PASS/8FAIL (`before.log`) on the published start source. Seven privacy/race cases and the absent-subscription lifecycle case failed; same-identity token refresh already passed. After:9PASS/0FAIL (`after.log`, final root log). The same assertions were retained.

## Implementation

- `src/TDA.tsx`: auth-scope wrapper, synchronous identity/epoch ref invalidation, and keyed content lifecycle. Account changes reset the component, including quiz/review/search display. Same-ID refresh does not remount.
- Auth subscription only updates refs/React state. No await, auth SDK call or RPC is executed inside the callback. SIGNED_OUT clears regardless of any stale supplied session; cleanup rejects old subscription callbacks.
- Start, question, answer and optional-detail boundaries combine the existing per-quiz version with the live account epoch. Fresh getUser identity is compared with the pinned identity; missing events cause a safe clear/remount before any answer RPC. Stale continuations stop before further SDK reads/RPC dispatch.
- Existing synchronous answer claim, uncertain-write handling, optional-detail recovery and score semantics are preserved.
- Three existing synthetic transports now model INITIAL_SESSION/subscription cleanup. Their original assertions remain unchanged. New fixtures/entry/browser wrapper are confined to this B QA.

## Observations and commands

- `npm ci --cache /tmp/poker-b-npm-20261026`: PASS.
- Full individual `tests/*.test.mjs`:278PASS/0FAIL across18 files, source SHA256 pinned in regression.json (previous277+one browser wrapper containing9 scenarios).
- `node tests/browser/tda-quiz.mjs`: existing6 mobile scenarios PASS.
- `node tests/tda-save-recovery.test.mjs`: existing4 root cases PASS (eight prior mobile scenarios + three installed-SDK fake-fetch cases within that count).
- `npm run build`: TypeScript/Vite PASS. Existing chunk-size warning preserved.
- `npm run lint`: PASS; existing warnings retained. No rule disabled.
- `git diff --check`: PASS.

Documentation-only review: https://supabase.com/docs/reference/javascript/auth-onauthstatechange and https://supabase.com/docs/guides/auth/server-side/advanced-guide . The subscription event is an invalidation signal; getUser remains the pre-RPC identity verification. No authorization is inferred from user_metadata/session presence.

## Limits and next gates

An already dispatched write cannot be undone by a client auth event. The tests demonstrate that its old response does not populate a different account and that optional follow-up reads are refused; they do not prove rollback, server idempotency, cross-tab cancellation, RLS or real SDK Auth-lock integration. These require reviewed isolated auth/DB evidence. Unknown subscription initialization refuses quiz work while public rule search remains accessible.

Official350 immutable snapshot, trusted answer key, official original/authorized translation and per-clause review remain BLOCKED. Synthetic question correctness is not official accuracy. Nothing is published.

Parent must save the tested descendant tree to the existing branch/PR119 and verify matching automatic CI. Local validation is not CI/main integration/production release. No new PR, heldSQLite write, reservation, controller adoption, production connection, deploy or billing operation occurred.

# DM single-flight and recoverable send boundary

Starting source: df0e31150ae9f1b68c337eecad9b7bfb36dc3a3f on the existing A branch. Fixed acceptance commit eee2541 contains three actual React/Chromium cases with synthetic, deferred transport. Before source repair all three fail: two concurrent block checks/inserts and a rejected insert leaving the UI busy. The first exploratory harness run used an ambiguous text locator; fixture-locator-error.txt is retained separately and is not a product failure. The corrected fixed input is before.txt.

DirectMessageChat now acquires a synchronous ref before block verification, holds it through write/reload, and releases it in finally. Returned errors and thrown transport errors preserve the draft and show generic guidance without raw server details. A confirmed write followed by reload rejection clears the draft and reports sent/display-failed rather than suggesting another write. No retry is automatic. Existing block verification remains fail-closed.

Seven actual mobile-sized React browser tests pass: pending-check and pending-insert duplicates, transport rejection/retry, returned write error/retry, blocked-check denial, confirmed write/reload failure, whitespace/IME. Every non-local browser request is aborted and the Supabase module is replaced before import. No production client or DB is used. This proves same-mounted-component single-flight only; cross-tab, uncertain network outcomes, server idempotency, RLS and realtime route races are separate gates.

All six root JavaScript suites pass: 96 tests/0 failures, including the seven new cases. npm ci, npm run build (TypeScript plus Vite), npm run lint and diff-check succeed; existing hook/chunk warnings remain. The A controller suites' 225 passing tests are separately recorded under journal-checkpoint-20261024 and not browser or production proof. No protected tests were modified, no dependency version changed.

Overlap review used the fresh 77-open-PR snapshot: 56 available HEAD source blobs exactly match the original DM file; the remaining 21 PRs' complete file lists do not change this path. Other-owner poll/video/tag work is untouched. New PR, workflow dispatch, production DB/deploy, main merge, host/controller activation and billing are prohibited and were not performed.

Next: fixed navigation/account/realtime generation-race fixtures, before any wider async refactor. Real auth/DB policies remain unverified. Server uncertainty cannot be solved by blindly retrying a write.

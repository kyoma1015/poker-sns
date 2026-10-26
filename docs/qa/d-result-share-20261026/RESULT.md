# D result loading and sharing lifecycle — 2026-10-26

Base c523f5473048615f6f8f937c0811a2ee6ea94d52. Existing Draft PR124 continuation only; publication and fresh exact-head CI remain root responsibilities. No main/DB/host/schedule/production action occurred.

## Existing patch inheritance

GitHub PR30's persona-audit delta was already present, so not reapplied. PR40's safe save/share messages and the request-lifecycle source inherited by PR60 (93d9948f8f829432fa66c5aafd294bf8924421fa) were compared with the actual component: this branch still had the older independent/unguarded request paths. Selectively reuse those question/result/load/share functions, not the whole older branch. Keep the present PNG cleanup/deadlines/cancellation and every existing score/classifier/presentation definition unchanged. The existing strict parseQuestions/LatestRequest helpers are now used by the real component. A synchronous share-pending lock supplements the ancestor's React state lock.

## Completion contract and tests

A requested saved result is shown only after its matching detail and ownership reads finish. Older request results/ownership cannot replace a later navigation, and unmount invalidates the pending lifecycle. Recoverable generic errors provide explicit retry actions without exposing raw transport details. Sharing keeps drafts on failure, clears cross-result drafts, refuses old writes when navigation/unmount precedes authentication completion, ignores late post completion, and suppresses duplicate same-tick submission. Restart clears the saved-result URL. A failed final submission retries exactly50 unique optionIDs without appending Q50 twice, and success persists the new result URL.

Fixed input is the separate test commit recorded in preservation.json. The same12 actual React/mobile Chromium cases against the pinned base reproduce0PASS/12FAIL in before.txt; after.txt records12PASS/0FAIL. save-before.txt is the earlier focused final-answer reproduction, not additional unique coverage. Test development initially used an ambiguous status selector; the final input uses exact generic public copy and was rerun against the unchanged base before recording the above counts.

All previously protected121 unit/actual-function tests PASS unchanged; previous7 actual PNG browser regressions PASS unchanged. Total140PASS/0FAIL (121+7+12), not a claim of140 unique live database checks. npmci, TypeScript/Vite build and lint exit0; existing warnings retained without suppression. The existing read-only, five-minute PR workflow adds the new browser suite after npmci; no new trigger/schedule, write permission, dispatch or budget expansion.

The mobile390x844 browser loads real React source with synthetic isolated RPC/auth/post transport. Non-local requests are blocked. Deferred old responses, rejection and repeated input are controlled by the fixture. No production API/DB credentials are imported. Successful browser tests do not prove actual RLS, server idempotency, physical iOS/Safari, backend result validation or classification accuracy.

## Remaining gates

Already-dispatched server posts are not rolled back by ignoring late client responses. Cross-tab/retry idempotency and account-switch authorization need reviewed backend policies and isolated realDB QA. This patch is result/navigation scoping, not a claim of atomically cancelling network/server work or all auth-state races.

Current bounded tracked-source search found no authoritative classifier/version, thresholds, tie order or expert labels; existing records explicitly classify those artifacts as missing. No global absence claim and no invented classifier. 36-animal reachability/boundaries/meaning remain BLOCKED. Inline legacy presentation/helper inheritance is a separate next review; raw reference960 agreement is not semantic correctness.

No score weights,50-question fixture,32-axis definition,36-animal inventory or diagnosis-v2 private schema changed. PollNO-GO and AUTO-RESUME OFF remain.

## Second bounded inheritance fix: actual presentation wiring

After preserving the lifecycle fix in1002657, review found the live component still contained older inline Number(value) coercion and raw-score ordering while the already-reviewed strict normalized src/playerTypePresentation.ts helper was present and unit-tested. PR60 ancestry already imported that helper. Three actual mobile browser inputs reproduce3FAIL/0PASS on the inline implementation: malformed/coercible scores invent positive traits; nonpositive values still make a top-three panel; different per-axis ceilings sort incorrectly by raw totals. See presentation-before.txt.

Selectively import the existing topPersonalTraits/personalAdvice functions and remove only their obsolete inline duplicates. The helper file, all32 ceiling values, copy/advice definitions, scoring/question fixtures,36animal inventory and classifier are unchanged. No new threshold or expert conclusion is invented. The visible behavior now follows the existing reviewed helper contract. Final-browser.txt records15PASS/0FAIL (old12+new3). Existing121 unit/actual-function and prior7 PNGbrowser reexecuted/PASS after this source change: final143PASS/0FAIL. build-final/lint-final exit0, warnings retained. Full method counts in regression-final.json.

The next safe D review is authoritative result-payload validation and authentic account-switch/ownership/RLS testing with a reviewed isolated backend; semantic classifier gates remain BLOCKED. Source/test/publication/CI state remain distinct.

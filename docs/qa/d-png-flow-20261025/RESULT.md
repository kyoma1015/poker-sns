# Diagnosis PNG save flow — 2026-10-25

This is the existing Draft PR124 continuation, not main integration or production verification.
Baseline source: 22ac8ce8eb858bca8d96aef636dd26e8a8fb7e5c. PR60's exact public PNG error-message correction was read from GitHub and selectively inherited; its whole older branch was not merged. Existing DOM exception cleanup remains intact.

## Feature acceptance

A mobile user can export a nonempty real canvas PNG, recover from image/encoding failure without raw exception disclosure, retry the same saved result, and avoid old-result downloads after restart/navigation or duplicate same-tick activations. Software callbacks have 15-second deadlines per image-loading and PNG-encoding stage; this does not promise a hard wall-clock bound when the browser/OS is suspended. Expired handlers/timers are cleaned and late encoding callbacks cannot change the rejected outcome.

Actual React + Chromium mobile390x844 uses in-memory fixture RPC transport, production imports replaced before loading, and all non-local requests aborted. Real artwork, canvas encoding and browser download are exercised; there is no database/network/production account validation. The 50-question historical fixture enables an actual quiz restart. The model's classification accuracy is not tested by this browser fixture.

Fixed seven browser cases at the pinned baseline: 1PASS /6FAIL (generic-error recovery, image deadline, PNG encoding deadline, restart stale download, same-tick duplicate save, saved-result navigation stale download). The same fixed input after: 7PASS /0FAIL. See before.txt/after.txt. Initial sandbox-only listen EPERM was classified as an environment failure, not a product failure; supported additional network permission enabled the local fixture server.

New helper boundary cases6PASS. Existing115 tests unchanged/PASS; total unit/actual-function121 plus actual browser7 =128 PASS /0FAIL. regression.json lists each directly executed test command/count; regression.log's file-level node --test summary is not used as method count. npm ci, npm run build (TypeScript/Vite), npm run lint succeeded. Existing lint warnings remain; image-operation effect state synchronization adds a warning and is not suppressed. Canvas timer behavior is synthetic-time-tested; real browser PNG success is not synthetic encoding.

Existing CI workflow retains its PR base trigger, prior commands, timeout, read-only permissions and absence of schedules; it now runs helper and browser suites. New CI is pending root publication; no local result is claimed as CI PASS.

## Remaining gates

Authoritative classifier/threshold/ties/expert labels remain BLOCKED. No scoring, question bank, DB, privacy/v2, RLS, ownership RPC or persisted-data contract changed. Broader historical result-load/timeline-post async inheritance requires separate review; this change scopes cancellation to PNG export only. Mobile Chromium is not iOS/Safari or physical-device QA. Main/prod/controller/scheduler remain untouched; poll NO-GO, AUTO-RESUME OFF.

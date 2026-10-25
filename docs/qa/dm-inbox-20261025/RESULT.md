# DM inbox account isolation and recovery

Pinned before source: fd818ff82f31c0901026b209f6c814da79df7b2c. This extends the already isolated conversation screen to the inbox; it does not claim server RLS or idempotency validation.

Completion contract recorded before source implementation: signout removes private previews; account switch cannot retain old previews; old reads cannot replace current/account results; rejected message/profile reads offer a redacted explicit retry; auth errors fail closed even with accompanying user data; unrelated rows are excluded and the query is scoped to the authenticated account.

The same eight real React/Chromium 390x844 synthetic-transport cases: original source **0 PASS/8 FAIL** (`before.txt`), updated source **8 PASS/0 FAIL** (`after.txt`). Every non-local browser request is aborted. These are browser automation with synthetic Supabase, not real devices, actual authentication, RLS or production QA. An initial profile-thenable fixture defect was corrected before the archived identical-input baseline; the experimental logs remain local and are not counted as product failures.

Implementation: synchronous auth invalidation without SDK calls inside auth callback; keyed account child; fresh getUser at each reload; generation identity checked after each await and before applying data; channel setup before initial snapshot; channel/subscription cleanup; client ownership filter as defense in depth; fail-closed generic errors and reload control. Existing rendering, profile fallback, unread counts, ordering and pull-to-refresh retained. No SQL/API/schema changes or new dependencies.

`runs.json` records exact full frontend/build/lint/automation/worker commands and logs. Existing PR121 workflow retains bounded permissions/budget and adds these source/test paths; no dispatch, schedule or host/controller adoption. Its exact-head result must be fetched after publication, not inferred from this local report.

Unfinished completion gates: authentic isolated DM schema/RLS/block policy and server-side idempotency; token revocation/network ambiguity; cross-tab/account real backend tests; notification/global unread integration and real-device QA. Client row filtering never substitutes for RLS. Existing protected45-job state is read only and not a development execution queue here.

# First-release server isolation follow-up — 2026-11-04 UTC

Assessed source: 7d52bdd51fda8ca6aaec1a9cded20d5acf685a63, Draft PR125.
Publication OFF / NO-GO. Gate count remains 4/12 PASS, 8 BLOCKED.

## Implemented preparation
`vercel.first-release.json` is an **unused, candidate-only** configuration. Normal vercel.json and ordinary App are unchanged. It specifies the canonical fail-closed build and dist-first-release, then rejects every /api and /share path before filesystem dispatch, including all future endpoints in those namespaces. No production/preview configuration is selected or deployed here.
The route contract regression checks 12 denied and 7 other paths, denial status/cache headers/order, and OFF/NO-GO/BLOCKED invariants. This is static configuration testing, not provider runtime proof. Encoded-path normalization, direct function domains, external Supabase REST/RPC/Storage, old clients, cached responses, and authenticated UI flows remain unproven. Do not promote nested_and_api_deferral based on this file.

## Confirmed bypass inventory (current source)
- vercel.json: /share/player-type/:id -> /api/share?type=player-type.
- api/share.ts: getPublicPlayerTypeResult and player-type branch fetch diagnosis with service-role credentials; public CDN caching exists. PR2 owns overlapping changes; not modified.
- api/poker-id-image.ts: card image endpoint remains outside initial scope; current visibility/owner validation preserved.
- src/Timeline.tsx: diagnosis detail RPC at431; latest diagnosis RPC769; poll composer/create RPC810–837; result link3212–3213.
- src/Profile.tsx: latest diagnosis RPC176–177; result links1081/1163.
- Direct Supabase RPC and Storage are different origins: a Vercel deny route cannot authorize or block these.
- FirstReleaseApp currently cannot mount any business page while OFF. Turning it ON without removing nested consumers is prohibited by the unresolved gate.

## Recovery and environment evidence
Management API reports running/connected, but one bounded read-only shell attempt still failed before execution:
bwrap: Can't create file /workspace/.git: No space left on device.
No shell retries, deletion, reset or recreation. Old PlayerSearch and diagnosis payload WIP remain UNRECOVERED; held SQLite remains unmeasured.
GitHub branch collection first100 returned no search/payload recovery branch; this is not proof of absence across every ref. PlayerSearch path history on PR125 includes088c762d,1b1973fa,485b176e,ca2f3a3c,fe4332b6. Current source has requestNumber guards; these are not evidence that the account-switch WIP was recovered.
No approved isolated Auth endpoint or credentials are configured in this session. No real JWT HTTP E2E attempted.

## Required next acceptance
1. Non-destructive environment capacity/inode recovery; exact original WIP diff recovery and read-only held-state verification.
2. Authoritative sanitized Auth/schema/table+column+inherited grants/RLS/RPC/Storage inventory with version/hash and isolated target receipt.
3. A/B/anonymous real Auth HTTP tests, revoked sessions/cache and owner denial matrix.
4. Candidate-specific nested content filtering and removal of deferred RPC consumers; preserve normal App and PR2 ownership.
5. Offline/provider-supported route normalization validation, then separately approved isolated runtime verification. No deployment is authorized by this preparation.
6. Authenticated mobile SNS10 flows. Current locked-page smoke is not that acceptance.
Original32-item ledger is unchanged. No GTO/video/production/main changes.

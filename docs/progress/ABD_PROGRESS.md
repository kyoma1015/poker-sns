# A/B/D progress measurement v1

Source scope: existing DEVELOPMENT_MASTER_20261024 / RELEASE_BACKLOG and current owner requirements. Frozen named catalogue: SNS19, TDA6, diagnosis7 =32 product feature units; audit5 and integration6 are control deliverables, not product features. This is a versioned known-scope baseline, not proof of an exhaustive atomic Poker ID backlog.

States: 未着手 = verified known work not started; 実装中 = partial/unfinished acceptance; 実装済み・未検証 = code acceptance present without tests; 隔離テスト合格 = declared isolated/mock acceptance only; 実DB認可確認済み = authentic actor/RLS acceptance in an isolated real DB; 統合確認済み = declared integrated acceptance; 公開可能 = all mandatory product gates evidenced, not permission to publish; UNKNOWN = missing evidence, never guessed as 未着手 or complete.

No arbitrary weights or stage averages. Product completion-evidence rate = publicly-ready evidenced required units / frozen named units. A 0% measured evidence rate does NOT mean no code exists; it means no whole feature in this catalogue has complete release evidence. Stage counts remain visible. Audit/preparation percentages count their evidenced finished deliverables at 統合確認済み or 公開可能; these are not deployment approvals. Whole Poker ID percentage is UNKNOWN because exhaustive scope and exclusive GTO completion evidence are unavailable. GTO is not changed or included in owned rates.

First baseline is retrospectively measured at75c13721fd8da6edefca3f97452040f59e3468fc under this policy. Earlier narrative reports had no comparable numeric rate. Future comparisons use the same IDs, definitions and suites; scope changes require a policy version/new baseline. Current/previous slots in ABD_PROGRESS.json are reused; do not spawn unlimited timestamp ledgers.

Same retained381 methods and browser93 baseline are separate from new next-navigation3 cases, new progress-policy8 methods and orchestration wrappers. New test count is not automatic quality improvement. The fixed three-case before input has measured1PASS/2FAIL at943173741c3c09ad56efa5bc93706b6f640fa9a7 / CI40352121918; after must be recorded only after real CI.

The JSON pins the last assessed source commit. CLI output adds the actual evaluated Git HEAD and timestamp, avoiding a self-referential commit hash. The publishing CI artifact/PR125 final record establishes the exact current checkpoint commit and outcomes. Self-validation results are not predicted inside the dataset before its CI executes.

Environment remains BLOCKED at sandbox creation (ENOSPC). Current capacity/inode/WIP/end-SQLite checks are UNKNOWN, not loss claims. Existing held blocked2 jobs are separate from this ledger's6 release blocker categories. No production, scheduler, controller, GTO, secret or billing operations are authorized by this policy.

## Separate implementation metric v1

Original release-readiness v1 catalogue, baseline, gates and rates are retained unchanged. Implementation never promotes release status.

Implementation uses the same 43 IDs (32 product units +11 control deliverables). Each IMPLEMENTED row requires an explicit source-level acceptance contract, commit SHA, pinned source/test Git blobs and successful exact-head CI. Database authorization, official TDA correctness and expert classification remain separate gates. File existence, old state labels or unrelated green CI cannot imply implementation.

PARTIAL means identified unfinished code. UNKNOWN means insufficient evidence, never zero or not-started. Exact implementation rate is UNKNOWN while any row is UNKNOWN. confirmed_percent = confirmed IMPLEMENTED / required fixed units is explicitly only an evidence lower bound, not an exact whole-feature completion estimate.

First implementation baseline retrospectively assesses previous PR125 HEAD3a4aaf5b9c68a8204b01cafea7ee3367879ff440; no earlier implementation measurement is invented. Contract/scope changes require a policy version. Existing release and test-suite comparison rules remain intact. Existing JSON slots and abd-progress artifact are reused.

Commands: node scripts/measure-abd-progress.mjs; node tests/abd-progress.test.mjs.

### Historical vs shallow checkout evidence
Full-history Selected ABD CI verifies every declared commit/path/blob. Shallow existing CI may lack historical commits: in that case it verifies every pinned blob against current file bytes and reports `current-bytes-only-historical-mapping-unavailable`, never historical-commit proof. Present historical commits with absent paths fail; every byte mismatch fails. No workflow, SQL or protected acceptance is changed to accommodate this.

### Current restart checkpoint — 2026-10-28
Measured before DM participant input:1PASS/2FAIL at aebe88d66346be4d3ea6d59f381aa7408d6fd831 / Selected CI40359352861. After3PASS at b5a103ee9ba8992c993626313049e967e3c415d0 / CI40611378547. Original19 DM cases retained; new three are separate. Never call the synthetic response defense real DB/RLS proof.
The previous b83dc8 metrics implementation had a Git blob header escape bug and required history in shallow CI; failed runs40360122177/40360122187 are retained as failures, not retried into a success claim. The hash now uses an actual zero byte and checkout proof modes are explicit;15measurement tests passed in40611378547.
Existing protected TDA filter/next input and deadlines remain unchanged. A new finite three-trial runner stops on the first failure, verifies reviewed acceptance hashes, preserves raw logs, and reports repeated executions separately from distinct coverage. Three clean trials are bounded evidence, not a root-cause resolution for the older timeout.
Workspace ENOSPC remains externally BLOCKED. Do not delete/reset WIP. A worktree /workspace/work/issue22-published-A-99587abe and D worktree /workspace/work/issue22-published-D-73baccf2 require actual path confirmation after recovery; these are prior reports, not fresh directory observations. Reopen exact local branches and inspect diffs before any migration. HeldSQLite not re-created or modified.
Authoritative DM schema/grants/policies are still absent in the inspected tracked SQL of pinned A99587abe; see its docs/workers/DM_ISOLATED_QA_REQUIREMENTS_20261026.md. D73baccf2 progress records classifier/threshold/tie/expert artifacts absent. No new original350 export or expert source was received. Do not repeat those synthetic audits as official certification.

### Verified follow-up checkpoint — 2026-10-28 01:09 UTC
At f6eff90b2b04347897a65369a34dda229fd9c8f5: Selected CI40612843054 and Poll CI40612843057 SUCCESS. Matching-query malformed content and matching realtime UPDATE each reproduce React child errors at bdf0f16 / CI40612457277 (0PASS/2FAIL); strict client DTO checks then pass both, preserve all prior22 cases, and add17 helper boundaries. This is not an RLS fix or production incident proof.
Same seven browser controls passed three unchanged trials (21 executions) with no retry or deadline increase. Their evaluated Git HEAD is the Actions synthetic merge commit, separately recorded from run.head_sha/PR head; no main merge was performed.
The Vercel PR status at f6eff90 is now success. VERCEL_RATE is closed with same-head GitHub status evidence; tracked open categories6→5. Deployment environment/public release remains unconfirmed; no manual Vercel operation, upgrade or bypass occurred. Product release rates stay0/0/0, audit40/preparation50; implementation exact rates remain UNKNOWN with separately reported confirmed lower bounds. Kept source scope, original release baseline and held blocked2 unchanged.
Last source results remain pinned to f6eff90. This metadata publishing commit must obtain its own CI; the final PR record resolves its result rather than predicting it.

### Authentication boundary audit — 2026-10-28 01:41 UTC (publishing CI pending)
Current environment management exposes status/network diagnostics only, not capacity repair or filesystem snapshots. One shell probe fails beforelaunch with ENOSPC; no repeat shell attempts or deletion/reset. Recovery must be performed by environment management while preserving WIP/state/.git/QA; it is not proven by running connectivity status.
Pinned ab80a3b / CI40615872296 reproduces3 unsafe acknowledgement attempts after delayed profile on missed account change, returned-auth-error and rejected-auth call; one normal control passes. Extended8026cc0 / CI40616296156 measures8 fixed cases:2PASS/6FAIL across read and send await boundaries. Prior24DM cases retained.
The pending source fix revalidates getUser after awaited profile/block work, refuses unverified UPDATE/INSERT, and routes incoming Realtime through the existing authenticated load path instead of an early duplicate acknowledgement. Added4Realtime cases are post-fix coverage, not separately measured pre-fix results.
authorization_inventory in ABD_PROGRESS.json pins actual DM table calls and four actual diagnosis RPCs plus posts. Underlying diagnosis relations, authoritative grants/policies/security context/idempotency and a confirmed disposable auth endpoint remain missing. No invented schema fixture is called real RLS proof; no production connection/SQL executed. Diagnosis p_is_public/classifier/threshold/scoring and other-owner v2 privacy design unchanged.
Official docs consulted: https://supabase.com/docs/reference/javascript/auth-getuser ; https://supabase.com/docs/guides/database/postgres/row-level-security ; https://supabase.com/changelog . Fresh getUser is only a client gate, not atomic DB authorization. No new TDA350 originals or classifier/expert artifacts received. Original B/D receipts remain authoritative for their stated limitations.

Verified client checkpoint:6e2aa4925974e41deace92fa438cb32fc68deb01 / Selected40616743682 and Poll40616743567 SUCCESS. Fixed8:2PASS/6FAIL→8PASS/0FAIL; supplementary4RealtimePASS; all36DM browser/old17DTO/old381regressions retained. Build/lintPASS (57warnings/0errors); unchanged TDA7controls x3PASS. Fresh identity checks remain client-side TOCTOU gates, not transactional server authorization. Backend role/grant/RLS/isolation proof remainsBLOCKED.
All32 product status/gate rows and implementation/release numerators remain unchanged. Existing5release blocker categories remainOPEN; previous Vercel-rate item remainsCLOSED at the checked source head. No public-ready feature is added by client QA.
Exact current docs/ledger publication commit needs its own CI; final PR125 record resolves it. Next check: after environment management confirms capacity repair (timeUNKNOWN), inspect A/D WIP once. No new schedule or repeated ENOSPC polling.

### 2026-10-28 authorization proposal continuation
Source review and disposable real-Postgres acceptance are recorded in docs/qa/selected-abd-20261026/authorization-review.md. Weak recipient-only UPDATE policy allowed content rewrite; rolled back. Candidate20PASS (CI40623657712), not authentic schema/JWT/RPC proof. Existing Selected regression526 node executions/0FAIL (381 retained; repeats/wrappers not unique features), build/lintPASS (57warnings) atfeacab/40623393013. A shallow historical-workflow mismatch in Poll40623393006 was addressed by restoring the original workflow and isolating model CI, without weakening protected assertions.
Frozen32 product gates/statuses unchanged, public-ready0/32, incomplete32; release blockers5 unchanged. Implementation exact rateUNKNOWN, confirmed9/PARTIAL5/UNKNOWN18 unchanged. PlayerSearch/payload WIP unreceived, heldSQLite inaccessible, no shell retry or source/state cleanup. Main/GTO/production unchanged. AUTO-RESUME OFF; pollNO-GO. Final publishing-head CI must be recorded in PR125 checkpoint.

### 2026-10-28 effective authority and public image guard
DM proposal effective grants now refuse inherited UPDATE, unreviewed permissive policies and BYPASSRLS actors atomically. Fixed6: before0PASS/1FAIL/5NOTRUN at e7de7a3/40625711891; after6PASS atdd19974/40626155417, original20PASS. This is not authentic schema/JWT proof.
Public-card image handler fixed12 measured9PASS/3FAIL at7f730d6/40626694807 for malformed/unrelated visibility rowsets. Strict single-owner response guard added; after result must be read from latest PR125 exact-head CI checkpoint. All calls are synthetic; no real service credential/DB/Storage used in these tests.77 other open PR file lists had no matching API/test path.
All32 product state/gate rows unchanged, public-ready0/32; confirmed9/PARTIAL5/UNKNOWN18, five release blocker categories unchanged. WIP/state unmeasured; no production/main/GTO change. AUTO-RESUME OFF, pollNO-GO.

### 2026-10-29T06:30:18Z recovered final evidence
Source345e99cb0a40b777bfd8acd624f6cdc265a3f22f was confirmed current/Draft/unmerged on resume. Actual executions were2026-10-28, receipts recovered2026-10-29; no fictitious new run times.
Selected40627094245 SUCCESS:538 Node executions/0FAIL (repeats/wrappers included), original381 preserved, card handler12PASS with same fixed input that previously measured9PASS/3FAIL. npmci/build/lintPASS,57warnings/0errors.
Authorization40627094184 SUCCESS: original20 plus new6 refusal/atomic catalog rollback assertionsPASS. Poll40627094185 SUCCESS:70PASS/0FAIL/0BLOCKED in existing disposable database. These are not authentic DM/diagnosis/Storage grants or live-data exposure evidence.
No product status/gate promotion across32 rows; publicly-ready0/32, confirmed implementation9/PARTIAL5/UNKNOWN18, five release blockers unchanged. PlayerSearch/payload WIP unrecovered; no shell retry, heldSQLite read/write, reset, production/main/GTO/schedule/billing operation.

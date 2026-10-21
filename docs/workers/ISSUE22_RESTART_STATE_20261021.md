# Issue22 restart state — 2026-10-21 UTC

Status: finite implementation and simulated-stop recovery verified; unattended continuous development NOT verified.

## Published outputs
|Lane|Draft PR|Controller source commit|Witnessed CI|
|---|---|---|---|
|A poll-only|#31|b90bd5f34c3791e4ad5da762c51f972a8d73710d|39572765844 SUCCESS, DB56/client30/mobile5|
|B saved answer validation|#32|ade6ba2a3436277f4ea1d530da34eaf04801a295|39572125844 SUCCESS at0639d36d720612466474e75fa8994f409d2d41de|
|C synthetic rank7|#33|2620396d207970fae7470043a404d7b0582b8829|39572168502 SUCCESS, fresh reconstructed native|
|Infrastructure|#34|b351e1fb0aeb6fe150e8ff038a76e3fd31bc90ac|39572524912 SUCCESS,13+22+15 safety tests|
|D doubleclick|#35|43e2bae1f5de33fc0d94a1d30b974492fbfbf238|39572865720 SUCCESS|
All repository URLs are https://github.com/kyoma1015/poker-sns/pull/N and /actions/runs/ID. Drafts are stacked on immutable input branches; do not merge predecessor and successor changes twice. PR13/21 are not wholesale release candidates.

## Actual recovery observation
D first task was BLOCKED by ignored node_modules files after provisioning. That source worktree is preserved. No scope guard or protected snapshot was weakened. New immutable input c477c81fa74f050e28cf99fe3ad67c8d1ffd497c moves cache to an owned external temp directory and uses already locked/npm-ci dependencies outside the source worktree.
Root prepared issue22-d-doubleclick-v2, injected a classified **simulated** quota stop before agent startup, closed that Python process, reopened the same SQLite in another process, resumed the same worktree with a new private lease, formally dispatched /root/d_next, then independently finished source/hash/browser acceptance and committed43e2bae. Thus real source implementation after a simulated stop/restart is witnessed. This does not establish real subscription quota recovery, a terminated chat restarting itself, or next-schedule execution. Public evidence under docs/qa/issue22-recovery-20261021/.

## Shared state continuity
Private state remains /workspace/work/issue22-host-controller/leases.sqlite. Verify original implemented IDs issue22-host-a/b/c/d and coordinator-retained spec hashes. Do not publish/copy the SQLite, private prepared tokens or receipts. Public checkpoint cannot reconstruct leases and cannot justify creating a new empty state. Missing state forces read-only reconciliation. Completed task IDs must not rerun; blocked first D task is retained for review, not stolen.

## Scheduler capability boundary
Existing enabled reservation remains interval6h/COUNT28, unchanged end policy. Prompt updated to consult this PR and to prepare missing failing-acceptance input descriptors rather than stop solely because task catalog is empty. Update succeeded; next_run_time is null and recorded run_details absent. This is not proof future execution will occur. run_now previously404 was not repeated. No daemon/runner service or paid API was installed. Library cannot inspect/unlock actual ChatGPT quota. Actual run budget activation requires verified original remaining count, unavailable in current automation response; do not reset schedule to28 or infer consumed count from wallclock.

## Safe next candidates (not runnable descriptors yet)
- [ ] A: production-catalog parity and real-DB UI/auth QA for poll; remains owner/environment gate, no production connection authorized.
- [ ] B: B-RULE-SEARCH-LATEST-01 — src/TDA.tsx raw search RPC unconditionally sets old results/error/loading; invalidate immediately on new query/clear, test out-of-order responses and throw recovery. Reference PR32 source searchRules and debounce effect. No corpus publication/SQL.
- [ ] C: C-CHECKPOINT-BUDGET-01 — gto/native/checkpoints.py verified_snapshot accepts NaN/Inf max_bytes, observed on own174-byte synthetic file. Require positive exact int before source open; test invalid types/bounds and old8 checkpoint cases. No old checkpoint access.
- [ ] D: D-RESULT-ERROR-REDACTION-01 — saveResult/shareToTimeline render backend Error.message; use fixed Japanese retry guidance without raw SQL/URL markers; test save/share/retry50/stale result preservation. No score/animal spec change.

Next host must commit protected failing acceptance to a new dedicated input branch, pin fullSHA/exact allowed and protected hashes/fixedprofile/risk/dependencies, collect fresh complete PR-file snapshot, and call plan. Candidate extraction produces review_required only; it is not automatic review. Overlapping divergent PRs must be reconciled, never bypass plan to force a task. No source implementation may start from these prose suggestions alone.

## Release gates
Poll isolated official Supabase DB/PostgREST56 PASS uses synthetic application schema and locally signed test JWTs; no GoTrue service or production-catalog parity. Remaining: actual schema inventory review, approved SQL/backup/disable runbook, migration history/advisors on working CLI, real DB UI/auth QA, deployment permission. Current Vercel403 remains unbypassed. GTO synthetic rank7/960-smoke are not G11 ground truth, strategy convergence or historical checkpoint compatibility. TDA official350 and diagnosis36 semantic correctness remain unverified. Main/production DB/deploy/billing untouched.

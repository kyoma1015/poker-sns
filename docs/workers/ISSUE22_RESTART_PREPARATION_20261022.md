# Issue22 restart preparation — 2026-10-22

Status: implementation preparation, NOT unattended development complete. No scheduler/controller activation or main/production/billing operation. The requested30-minute native automation cadence is unsupported by the available official automations tool, whose maximum frequency is once per hour. Do not approximate it by staggered tasks or replace it silently.

## Current restoration and provider facts
Main781f038415503ece850c25a26e72ef67dee9c8a1 and Draft100–105 exact heads were reread. Previously pending39785868353 is now SUCCESS. Original durable4 spec hashes match; initial state36implemented/2blocked/no running job. New work is separate from those completed IDs. Source manifests/plans/results are under docs/qa/issue22-restart-preparation-20261022/.

Read-only official automations.peek found existing Poker ID6h/COUNT28 enabled, last_run2026-10-22T10:54:27.935759+00:00, next_run_time=null; run_details absent. Its independent one-off probe is disabled/consumed. Null-field cause UNKNOWN; this is not proof the recurrence is disabled or exhausted. Historical prompt arrival in an active host is preserved in INDEPENDENT_LAUNCH_20261021.md; it is not a fresh independent Codex coldstart/code completion. No run_now/old EROFS probe/HOME relocation/credential copying was retried. Actual account task timezone is America/Los_Angeles; do not substitute the workspace timezone for scheduling.

## Feasible options and limits
| Method | Next launch / cadence | State/exclusion/auth | Cost and stop/recovery |
|---|---|---|---|
| Official ChatGPT automations | Supported scheduled prompt mechanism; shortest60min. Current provider runID/Codex host binding not exposed/verified. | Same persistent host path and tools on a later invocation UNKNOWN. Root must verify original anchor before writes; never reconstruct private state from public JSON. | Existing-plan allowance/quota not observable; no new paid API. Native disable action exists but was not invoked/tested. Finite2-run read-only probe proposed, not registered. |
| GitHub Actions | Workflow scheduling can initiate CI; no verified bridge to this ChatGPT Work/Codex host. Existing queue workflow is validation-only. | RUNNER_TEMP SQLite is ephemeral and cannot replace shared leases. Existing connector authentication is not assumed usable by a child Codex process. Default-branch installation/new rights require approval. | Existing CI works; remaining free quota/billing settings UNKNOWN. No model API keys or service added. Cancellation is CI stop, not proof a separate model stopped. |
| External persistent runner + Codex CLI | No authorized persistent runner/model launch demonstrated here. Known managed CLI EROFS remains BLOCKED, not retried. | Requires explicit persistent host/auth provisioning and reviewed sandbox. No credential copy or constraint bypass. | Price/hosting/subscription setup UNKNOWN; paid/new services require approval. Not selected. |

Selected preparation path: keep the established host-session/controller stack. First prove a supported provider can deliver independent readonly callbacks with the same tools/state. Only later, after reviewed global guard adoption and explicit controller activation approval, connect actual source dispatch. New frameworks/cloud services were not scaffolded: this is an existing non-eve stack and user forbids unapproved services.

## Concrete, disabled approval proposal
HOURLY_RESTART_PROBE_PROPOSAL_20261022.json contains the exact bounded read-only prompt and proposed create arguments: hourlyCOUNT2, first run relative+1hour, inherited account timezone. It is data only, enabled=false, no workflow/provider action consumes it automatically. Requires explicit approval to change the requested cadence, pause the existing6h reservation during verification and register the finite2-run probe. No existing reservation was changed/extended, and no probe was recreated.

The probe does NOT acquire leases, modify SQLite/source/GitHub, start workers, register follow-up tasks or enable a controller. It checks actual independent invocation metadata, supported execution/collaboration/GitHub capabilities, retained state anchor and completed IDs. Missing tools/state or provider runID are reported as BLOCKED/UNKNOWN. COUNT2 completion ends the experiment without extension. If creation fails after an approved pause, preserve the error and request/reconcile the known prior state; do not blindly reactivate over a newer emergency stop.

## Prepared implementation components
1. Publication checkpoint API extends existing Continuation, not a second controller. record_publication stores only12 typed public metadata fields plus taskID/revision/time: source/head SHA, branch/PR/CIrun/CIattempt/status, owner/runID, last_success/next_action, observed retry count. It requires implemented job/source-commit match; retry count comes from existing attempts. BEGIN IMMEDIATE/CAS prevents stale concurrent overwrite, source/branch/PR identities are immutable, timestamps finite/nondecreasing. public_checkpoint does not export raw private evidence/context/token. The API was tested only on owned temporary state; live schema is untouched.
2. Whole-invocation guard is opt-in preparation. It reuses existing setup_lock and reserve_run rather than another queue/lease/budget store. It is not installed in the active host or worker. Draft107 source/local proof and queued CI are recorded in this QA directory.

## Safety / operational gaps
- Existing per-task/per-lane lease and hash/acceptance gates remain required. Unknown-live running jobs, including expired rows, cannot be stolen. An OS lock recovered after a test process dies is not permission to claim an unknown live source worker.
- New guard is cooperative and local-filesystem/process scoped. Every real controller entry must adopt it consistently before global exclusion can be claimed. Shared filesystem locking semantics on another host remain unverified.
- Emergency stop prevents new entry and must be checked between dispatch/checkpoint stages. It does not kill an already-running agent or prove it stopped. Defer only after actual agent liveness is confirmed stopped; existing defer/resume checks stay intact.
- Existing quota/transient recovery permits at most one retry and stops auth/permission/unknown errors. It is bounded delayed retry, not a completed global exponential-backoff/circuit-breaker service. Provider availability cannot be externally detected/unblocked here. A cross-invocation consecutive-failure breaker and verified cost telemetry remain work before unattended source activation.
- Existing run cap is reused, never reset/extended. Preparation tests do not demonstrate that every historical/manual invocation booked that cap. No runtime rollout occurred.

## End-to-end acceptance status
| Requirement | Evidence/status |
|---|---|
| Real independent Codex launch | BLOCKED: official scheduling prompt API exists; next independent Codex execution environment/identity unverified. |
| Automatic next invocation after exit | UNVERIFIED; no new activation authorized. |
| Retained checkpoint read | Current manual host continuity PASS; later coldstart UNVERIFIED. |
| Completed task no replay | Existing tests/state IDs preserved; later independent run UNVERIFIED. |
| Global exclusion | Prepared component/temp process tests only; active controller integration UNVERIFIED. |
| Safe recovery | Existing stopped-host fixtures/source evidence retained; provider failure/coldstart recovery UNVERIFIED. |
| Emergency stop | Prepared cooperative component only; provider disable/active-worker stop not tested. |
| Run/cost limits | Existing finite-cap tests; account cost/quota telemetry UNKNOWN. |
| CI/log/provider IDs | Component CI is proof of isolated tests, not scheduler launch. Provider runID absent. |

## Restart checkpoint
RUN_CHECKPOINT_20261022.json records this host invocation, completed new IDs/PRs/source/CI, last success/next action, owner/retry/time and blockers without private receipts/tokens. It is a public progress record, not authority to dispatch source or reconstruct missing private leases. Verify current GitHub heads/CI, original state anchor and running jobs first. Only reviewed immutable FAIL descriptors can enter existing prepare→formal agent→receipt→finish. Never replay implemented IDs. Scheduler/controller activation still requires explicit user approval.

Poll remains NO-GO; no poll/backups feature edits, Supabase production connection, Vercel, main merge, paid service or secret registration.

## New source evidence and emergency procedure
- Draft106, source3a9176c388707d8b4f7121cfc1b9f83ee2a23556; fixed76 methods/subtests initially30errors→76PASS, worker22/queue15PASS. CI39795238064 was queued with no runner assigned at observation, not a test failure or PASS; no rerun/cancellation.
- Draft107, sourcef71e823ddffd147664bba0aee7062d991155745d, CI-only head6d2f4834d3a06abb61058fcebca952f360ec0f45. Fixed85/9ERROR→85PASS, worker22/queue15PASS. Includes real owned-temp childprocess exclusion/process-death lock recovery; not independent scheduled host proof. CI39796232980 queued, not PASS.
- Both source tasks used existing formal host prepare→agent→trustedreceipt→finish with protected hashes and source-only commits. Real state now38implemented/2blocked/running0; new publication schema absent from live state. These are local source completions; CI is recorded separately.
- A future approved caller holds guard at /workspace/work/issue22-host-controller/leases.invocation.lock and checks /workspace/work/issue22-host-controller/leases.stop. These real files were not created/touched here. Emergency procedure: disable future provider callbacks, set stop flag through authorized host, observe actual worker stop before defer/recovery, preserve state/worktrees/receipts, reconcile hashes and owner, then explicit approval before clearing stop/resuming. Disabling a reservation alone does not terminate active work.
- Do not promote the disabled probe proposal into an implementation worker. Its two callbacks are read-only and cannot run source even if tools are present. Further controller activation/global breaker/cost review is separate.

CI queue observation: both new component runs remain queued/runner unavailable at last check. Cause UNKNOWN; no retry/cancel/permission or billing operation. After the finite readonly probe, do not automatically re-enable the old reservation or extend the probe; obtain the next explicit approval.

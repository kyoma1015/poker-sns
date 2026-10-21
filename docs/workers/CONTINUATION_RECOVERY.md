# Reviewed continuation and host recovery

Implemented component: `scripts/continuation_recovery.py`. This extends PR26; it
is not a daemon, a new scheduler, an external quota detector, or proof of a later
unattended implementation. It performs no network, production DB, credential,
billing or deployment operations. Formal host collaboration remains necessary.

## Replenishment contract

`extract_candidates` turns unchecked Markdown checkboxes from bounded
host-provided MASTER/Issue/QA snapshots into **review_required suggestions only**.
Untrusted text never supplies executable commands or becomes a ready task.
A trusted host must review a precise task descriptor, record its purpose,
execution/completion conditions, dependencies, references and low/medium risk,
pin its full baseSHA, exact writable paths and protected tests, and independently
witness a failing fixed baseline. The baseline includes test count, profile,
baseSHA and exact protected-file SHA256s; this is a coordinator attestation,
not cryptographic evidence of review or model identity.

`Continuation.plan(candidates, observations, repository)` verifies Git object
existence/protected hashes, fixed allowlisted profiles and immutable IDs. It
requires a complete PR head/file snapshot at most120s old. Existing tasks,
active lane leases, unmet dependencies, duplicate branches and overlapping
open PR paths block dispatch. Reviewed `inherited_prs` may explicitly permit a
known PR's paths only if the exact observed headSHA is pinned and Git ancestry
proves that head is contained in the candidate base. This is not permission to
merge both PRs blindly. One candidate per lane, at most four per plan. A plan is
not a lease or an implementation; use PR26 prepare → formal dispatch → finish.

No real candidate catalog is silently synthesized or activated by this module.
The host must supply fresh GitHub observations and reviewed immutable descriptors.
When only suggestions exist, save them and stop that lane rather than weakening
acceptance or inventing a product specification.

## Durable state and finite invocation bounds

Open `Continuation(state, anchor)` only against the **existing** shared lease DB.
The nonempty coordinator-owned anchor maps previously known immutable job IDs to
their spec_hash. Missing/symlinked state, missing schema or mismatched anchors fail
closed. Do not replace lost state with an empty database. Public checkpoints can
help reconcile GitHub PRs but cannot reconstruct private leases or prove no
worker is still active. Instance replacement still requires a genuinely durable
state store; publishing SQLite or private receipts is prohibited.

`reserve_run(id)` atomically records distinct invocations with a local upper cap
of28. Duplicate invocation IDs are rejected across process restarts. This local
counter **does not preserve or restart the existing finite reservation by itself**.
Before an actual scheduled launcher uses it, import the verified remaining count
of the original reservation with `restrict_remaining_runs(remaining)`. This can
only shrink the persisted local limit, never extend/reset it. If the scheduler's
remaining context is unknown, do not launch. No reservation was changed here.
The host must still impose its30min batch and180s worker limit; this planning
library is not a replacement for the scheduler/host timeout boundary.

## Safe stop and one delayed retry

The trusted coordinator must stop the real formal agent first and call
`defer_host(id, PRIVATE_token, kind, agent_stopped=True, ...)`. Only coordinator
failure classes are accepted, never raw exceptions: quota/transient may receive
one delayed retry; authentication/permission/runtime/unknown become BLOCKED.
The component cannot directly inspect or clear a ChatGPT/Codex account quota.
It can consume a witnessed host error and a bounded retry timestamp (1s..24h).
A retry is an attempt when permitted, not proof quota has recovered; another
failure exhausts the task's two-attempt cap. No CLI EROFS probes, HOME/CODEX_HOME
moves, credential copying or sandbox bypass are introduced.

Before deferring, the checkpoint verifies unchanged HEAD, unchanged protected
acceptance, strict allowed paths, no symlink/deletion/escape and SHA256 of all
retained sources. Context and checkpoint stay private in the same SQLite DB.
`resume_host` reopens that state, waits until retry time, rechecks the checkpoint,
uses the existing lease transaction for lane exclusion and renews the same task
with a new token while preserving its worktree. The returned receipt is PRIVATE:
never give it to the model or GitHub. A successful resume is only **prepared**;
the host must dispatch its actual formal collaboration agent and later invoke
`finish_host_session` with an independently witnessed trusted receipt.

Expired/crashed leases are not stolen or automatically recovered. Unknown agent
liveness, changed retained source/protected tests or missing state requires safe
stop and coordinator review. Keeping a worktree is not a claim that arbitrary
in-flight execution can resume safely after a crash.

## Verification and limits

Protected acceptance under `tests/worker_acceptance/test_continuation_recovery.py`
uses isolated Git repositories/SQLite and verifies candidate gates, continuity,
finite-run/replay exclusion, next-task selection, deferred quota-equivalent
stop/reopen/resume, retained source, actual fixed tests and a controller commit,
one retry only, permission failure stopping, checkpoint tamper rejection and
safe public export. Fixtures explicitly set `test_fixture=true`; they are not
proof that a new unattended AI or later schedule invocation ran.

The read-only GitHub workflow also executes the existing22worker and15queue
regressions. Root should record the published commit/actual CI result separately.
No production release, GoTrue verification, account-quota recovery, persistent
scheduler installation or future cold-start-to-code completion is implied.

## Dependency provisioning remains a separate gate

Do not run `npm ci` or create ignored dependency files after the host has captured
its protected preparation snapshot and treat those deltas as model source.
Provision verified pinned dependencies before source dispatch using a separately
reviewed setup lifecycle. No ignored-file/path guard was weakened by this
component, and no API to bless arbitrary dependency deltas is provided. If a
prepared worktree acquires unexpected node_modules/ignored deltas, preserve it
and BLOCK rather than manually replacing the snapshot to obtain PASS.

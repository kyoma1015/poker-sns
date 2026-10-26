# Automatic restart capability and approval boundary

Status: AUTO-RESUME OFF; independent automatic Codex startup UNKNOWN. This review does not activate a schedule, host or controller. It is not a replacement controller implementation.

Official automations.peek was used read-only on the saved two-occurrence probe6ada2596d5148191be6c9dbf73ec2d34 and original six-hour task6ad6f43503cc8191b11915fdbaa51312. Both are disabled and next_run_time=null. Probe last_run_time remains2026-10-22T16:57:54.154987Z; original task last_run_time2026-10-22T10:54:27.935759Z. Neither returns provider last_run nor latest_result run ID. The probe's second configured17:02:46Z occurrence differs by291.845013s from that last_run_time. Without scheduled_for/start/end/run ID, no association or successful two-run exhaustion can be inferred. The reason for null next_run_time remains UNKNOWN; disabled status alone is not an exhaustion log. Settings were not changed.

| Mechanism | Observed capability | Missing condition |
| --- | --- | --- |
| Active Codex conversation/collaboration | Authorized source edits and local processes can execute now | Not an independent future-start service or quota-recovery listener |
| Existing PR GitHub Actions | Standard public Ubuntu jobs execute bounded tests/builds; PR119/120 automatic runs succeeded | CI has no formal host collaboration tools, persistent held workspace or approved model startup identity; it is not an AI code worker |
| Official finite conversation automation | Saved finite reservations exist; read-only status lookup works | Old reservations disabled, no provider run IDs/results; new reservation is not approved and must not be assumed to create this same durable host |
| Existing Continuation/InvocationGuard/journal/checkpoint | Isolated recovery, finite counts, UNKNOWN refusal and state retention are tested | Actual trusted store auth/durability/callback deadlines and formal host connection not approved/proved |

The prior manual continuity algorithm is now scripts/inspect_retained_state.py, with12 temporary-state tests. A new host can invoke it to restore a sanitized observation without creating SQLite or acquiring a lease. Current real observation45/43implemented/2blocked/running0, original4hashes, all-row digest, run1/limit28 and protected checkpoint match. PASS still means execution_allowed=false: fresh PR/CI observations, descriptor review, permission and positive liveness remain separate requirements. Root used existing GitHub tools to read current main/PRs/CI; no second queue/lease/scheduler was introduced.

Usage-limit reset/解除 time is not exposed by the available provider records. Existing bounded recovery can save a reason and an official retry-after time when one is actually supplied; it cannot invent one, override a quota or launch a session after this host terminates. Restoring a checkpoint and retaining a task is not proof of future provider execution.

## Concrete requirements before a future finite probe

1. Explicit approval for a new finite schedule (example proposal only: hourly,2 occurrences, max30min each, concurrency1, no new spending); never reuse/reset the old occurrence budget.
2. An authorized provider connection that demonstrably starts a Codex execution, reports run ID/scheduled_for/start/end and preserves the same approved durable workspace identity. Reservation registration alone fails acceptance.
3. Approved reviewed task descriptors, source/acceptance hashes and scope; explicit permission for any needed held lease/job writes or a separately reviewed durable state design. Current held state remains read-only and oldBLOCKED immutable.
4. Existing permitted GitHub publisher/model identity with known quotas/budget; no secret copying, new paid API/key registration, auth bypass or credentials in logs/checkpoints.
5. Trusted external store with authenticated atomic CAS, durable intents/pins and finite deadlines; verify stop, liveness UNKNOWN refusal, finite reservation accounting, artifact recovery and emergency stop before real host connection.
6. Two independently witnessed provider runs must read the prior state, avoid completed IDs/duplicate PRs, save results and stop at the approved limit. Only then evaluate a separately approved development trial; no unlimited operation.

No activation approval is requested merely to continue the current safe source work. Missing launcher approval/records stays BLOCKED while independent product development continues. Poll publication NO-GO; main/production/controller adoption remain prohibited.

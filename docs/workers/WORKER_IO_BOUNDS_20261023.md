# Issue22 PR112 follow-up: stdin, cleanup and UNKNOWN safety

Manual invocation began2026-10-22T18:25:49UTC. BasePR11205ea4bf2ea076279f92aafda5266edfdab7e475f, itself an unmerged Draft. No controller/main/scheduler activation.

## Reproduced failures and minimal scoped fixes

Four immutable test phases are preserved in docs/qa/worker-io-bounds-20261023/fixed-inputs-and-protected.json:

- b8695ba input:5tests/4FAIL. Stdin backpressure prevents timeout and stop checks; cleanup can enter unbounded Popen context wait; run_task releases UNKNOWN liveness as blocked.
- 9c0ed83 input:1test/1FAIL. finish_host_session also releases an unconfirmed acceptance process and loses its prepared recovery context.
- 0631b33 input:4tests/1FAIL. An observed setsid grandchild survives group cleanup without UNKNOWN propagation.
- 68f1be5 input:5tests/4FAIL. Ordinary expiry can erase UNKNOWN context and acquire same/other lane tasks; metadata permission denial is conflated with known process disappearance.

These are phased baselines, not a claim that all15cases ran at one initial SHA. All old13protected test files remain byte-identical to PR112, and all five new test/helper files match their pinned inputs (18file hashes).

Source changes are confined to scripts/code_worker.py:
- Start executor deadline before spawn/input. Send stdin with nonblocking os.write; check deadline/output budget/trusted opt-in stop hook before/through input and after cleanup. No real CLI/auth probe is performed.
- Remove unbounded Popen context exit/wait. Shared cleanup sends TERM then KILL to the owned group with wait timeouts.2s/.5s, then polls known descendants for at most.2s. Original exceptions retain identity and receive an UNKNOWN note/attribute when cleanup is unconfirmed. Successful publication is refused on unconfirmed cleanup.
- UNKNOWN keeps running lease ownership instead of finalizing the row. Host prepared task/worktree/base/protected context is retained. CLI run_task preserves files/running evidence but is not claimed to have complete host-resume context.
- Before any expiry mutation, Leases.claim refuses new claims across lanes if a running row explicitly records UNKNOWN. Expiry cannot erase that context or silently create another task. Positive stop/ownership review remains required; no forced takeover/reset is added.
- Linux metadata snapshots inspect only process stat topology/start identity, not environment/command lines. ENOENT is distinguished from inaccessible/unparseable metadata. Observed live escaped descendants become UNKNOWN; the controller does not kill them by PID outside its group.

## Witnessed QA

Final new15casesPASS; ten rounds150/150PASS. Existing acceptance85, worker22, queue15, controller9, recovery lifecycle8 and command1 allPASS. Expected dedicatedCI290 executions, no failures. The old testcase/fixture proof is not weakened.

Actual OS fixtures verify pipe backpressure, stop during input, parentSIGKILL during input, partial source file preservation, TERM-ignoring parent/child/grandchild→SIGKILL, and waitpid-reap of child/grandchild by a **test-only isolated subreaper**. A setsid grandchild survives group cleanup and is classifiedUNKNOWN, then explicitly cleaned by its owning fixture. This is not automatic cross-session termination. Permission denial is fault-injected around real Popen waits and separately tested with bounded fake waits; it does not change real permissions or bypass a platform restriction.

PID, elapsed, signal and reap observations are in owned-tree-metrics.jsonl and a seven-day bounded CI artifact. Linux-only /proc/subreaper scope is explicit. All probes use owned temporary files/processes/DBs and synthetic executables/catalogs/receipts; this is not real model/independent scheduler proof.

## Time and liveness limits — not universal guarantees

Explicit wait-call budgets total.7s plus up to.2s known-descendant polling. No wait(None) or Popen context exit remains on these paths. This bounds those software waits; /proc traversal, kernel calls, Popen creation and the trusted callback itself are not a hard all-OS-state wall-clock SLA. A stuck kernel or untrusted/blocking callback is not proved recoverable. Snapshot scanning is capped; leader exit before observation, later forks, hidden/unobserved descendants and PID/PGID races still require stronger runtime containment. Known observation denial remainsUNKNOWN, notPASS.

## Host-call boundary audit

The new trusted optional callback brackets the executor/input path. Existing prepare_host_session/finish_host_session and legacy main do not automatically inject InvocationGuard checks around formal collaboration dispatch. The host coordinator must explicitly check before/after calls and positively establish agent termination. This is an unadopted integration gate, not silently activated functionality. Existing temporary-Git recovery tests retain uncommitted files, validate protected/base/source hashes, consume at most one retry, refuse duplicate runIDs and progress to a reviewed fixture task without resetting its finite limit. Actual formal-agent cancellation/coldstart is unproved.

Independent read-only review of the earlier51751b9 phase found the expiry/metadata-denial flaws; both were then fixed with the additional68f1be5 baseline. Its remaining warnings about unobserved descendants, CLI versus host context and wall-clock claims are retained above. This is not formal GitHub review approval.

## Retained state and restart

Retained SQLite is mode=ro only:45total/43implemented/2blocked/running0, original4hashesmatch, logicaldigest281bd3a0b00057eef2a00cdd5d7283d8cc8f4031f39f029c63c5af8533670ada. Checkpointb8afdc9feb93d142f723c41850d5806c0efc5917cafe6cd2324255cdab2555c0 and run records/local limit1of28 remain unchanged; they are not provider remaining permission. No retained job/lease or real development descriptor is created. Old blocked2 remain untouched.

Main remains781f038415503ece850c25a26e72ef67dee9c8a1. PR38/69/74/103/106–112 source scopes were rechecked; no existing patch is reapplied. New work is a stacked Draft on PR112; no main merge, controller switch, reservation change, billing/Supabase/Vercel/poll release. Independent automatic launch remainsUNKNOWN; unattended developmentOFF; pollNO-GO.

Next: review this exact source/CI stack, then separately design the formal-host boundary adapter with approved real-task and liveness evidence. Kernel containment/unknown supervision and actual provider launch remain separate gates. Do not replay oldcompleted/blocked IDs or enable a scheduler to make a fixture test look autonomous.

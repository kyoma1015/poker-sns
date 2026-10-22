# Issue22 interruption, bounded recovery and continuation QA

Explicit manual execution began2026-10-22T17:52:54UTC (2026-10-23 02:52:54JST). BasePR1119068971e8571e3bd162b8173a42d735be0c969b9, itself stacked on unmergedPR107. No retained controller, production service or scheduler is activated.

## Root causes and remaining boundaries

| Cause | Evidence and classification | Recovery condition |
|---|---|---|
| Worker leader exits but descendant survives timeout | New fixed failure at code_worker.py:265: old finally cleans the process group only while leader is alive. Actual CodexExecutor method invoked a controlled executable whose child ignores SIGTERM; old method returns while child is executing. FIXED in candidate only. | Always SIGKILL the owned process group during final cleanup; wait/reap the direct leader. |
| Cleanup error masks original initialization failure | PR111 continuation_recovery.py:78 closes the owned connection, but a close exception replaces the original DDL exception. Injected two-error case reproduces identity failure. FIXED in candidate only. | Preserve/rethrow original exception and attach a constant cleanup-failure note without raw exception data. |
| Controller process is killed while a separate-session worker lives | Actual controller process uses InvocationGuard and prepare_host_session, then is SIGKILLed; its worker survives and job remains running. OS invocation lock is released but guard rejects a replacement coordinator. EXPECTED fail-closed boundary, not fixed by takeover. | Coordinator/operator must positively stop/confirm owned worker, retain context, defer before lease expiry, then resume through the existing one-retry protocol. |
| SQLite WAL bootstrap race | Historical audit39817880993 attempt1/job119961040154 failed journal_mode=WAL; attempt2 success was not a fix. PR69/38 initialization fix already inherited. Existing85 and PR1119 tests run again successfully; not reimplemented. | Use the reviewed initializer and owned temporary DB stability tests; no live adoption inferred. |
| Lease expiry/owner mismatch | code_worker.py Leases.finish/claim and continuation_recovery.py:351/387 reject invalid ownership, unconfirmed liveness and expired/replayed context. Existing recovery acceptance passes; new actual-process tests preserve running state until liveness confirmed. | No force-steal or run reset. Expired/unknown live jobs require review; valid transient/quota deferred jobs may retry once. |
| Checkpoint/CAS failure | PR1119 tests cover four-process CAS winner1, SQL rollback, SIGKILL mid-transaction and committed-state survival. Existing protected tests reject changed HEAD/protected/source hashes on resume. PASS within isolated cases. | Revalidate original anchor, HEAD, protected tests, source digest and not-before; reject tampering/stale revisions. |
| CI interruption/cancellation | recovery workflow cancel-in-progress:true and five-minute cap are configuration facts, not proof a specific prior run was cancelled. Historical WAL failure has concrete evidence. New synthetic publication test records failure/blocked, then accepts a fresh revision without rerunning completed source. | Inspect actual run/job logs; preserve source commit; classify and fix cause before a bounded rerun. No deliberately induced public CI failure or autonomous CI-repair worker is claimed. |
| Next task is not automatically dispatched | code_worker.py:484 main runs one finite manifest and returns. Continuation.plan:264 returns descriptors, not a dispatcher/daemon. At observation, all seven retained ready-next candidates are implemented or historicalblocked; retained45jobs contain no pending/running job. | New real source dispatch needs an existing reviewed executable descriptor, fresh overlap evidence, allowed invocation budget and host adapter. No new real task is created here. |
| Codex session/time/quota/disconnection | Host/provider runtime end reasons and remaining subscription allowance are not exposed here. UNKNOWN; existing CLI EROFS probe is not repeated. | Save/revalidate retained context within approved opportunities; auth/permission/exhaustion remain BLOCKED, never bypassed. |
| Provider timing difference | Formal peek: stopped COUNT2 probe still has no last_run/latest_result/runID/start/end/history, last_run_time16:57:54.154987UTC vs expected17:02:46UTC. UNKNOWN291.845013second discrepancy. | Obtain official provider dispatch history; no new reservation/resume/extension. |

## Fixed input and source changes

Input77f1c96c581594f660038096cfef107759749f12 adds eight fixed lifecycle tests with unchanged PR111 source:8tests/2FAIL. Source87232734b26e98d8e7a10a437394708bd1ec6743 changes only code_worker.py(+6/-2) and continuation_recovery.py(+5/-2). No guard, lease, checkpoint, retry, schema or budget semantics are relaxed. PR111 remains Draft/unmodified; this is a separate stacked candidate.

All ten existing protected acceptance files, PR111's controller integration test and the new input-pinned lifecycle test remain unchanged, with12file SHA256 proof in docs/qa/worker-recovery-20261023/protected-hashes.json. PR38/69/74/103/106–111 heads/base/changed paths were read from GitHub; reviewed-pr-snapshot.json records the scope. GTO/Unicode/UI/poll files are untouched.

## Witnessed continuation, not just stopping

The tests call actual prepare_host_session, defer_host, resume_host, finish_host_session, plan, record_publication and InvocationGuard APIs on owned SQLite and real temporary Git repositories/worktrees/commits. Executors, reviewed catalogs and trusted receipts are explicitly synthetic; test_fixture:true produces real_ai_implementation:false. No live Codex executable, credentials, remote model, collaboration identity or GitHub publication is simulated as successful real AI execution.

1. Under owned-run-1, prepare a fixture task and launch an OS process that writes an uncommitted source fix.
2. Create stop, observe guard.check refusal, verify defer is rejected before agent_stopped confirmation, SIGTERM the worker and observe exit-15.
3. After observed termination, defer transient with bounded delay; leave worktree/source/protected tests intact.
4. Close/reopen the controller from its original anchor. Before not-before, resume returnsNone.
5. Under owned-run-2, verify the same worktree and bytes, reacquire one retry lease, execute fixed acceptance and create a real local commit through finish_host_session.
6. Completed task cannot resume/prepare again. The next synthetic reviewed B task is planned, prepared, tested and committed within the second invocation.
7. Both old runID replay and third invocation are refused. Owned run_count2/run_limit2 remain2; no counter reset. A second transient or authentication/permission failure becomes blocked.

A separate process-death case SIGKILLs the real test controller (exit-9), observes its live worker and retained running context, proves a replacement guard cannot enter, then positively terminates that owned worker and uses the same bounded recovery path. Existing uncommitted bytes survive. This is coordinated/manual recovery, not automatic recovery after lost supervision.

## Executed results and limitations

- Fixed8:2FAIL before→8PASS after.
- Ten repeats:80/80PASS. Existing acceptance85, worker22, queue15, PR111controller9 allPASS.
- Local stop request→fixture worker exit-15:10samples,0.000473–0.001104seconds. Timeout0.8s→executor return and descendant non-execution:10samples,0.803613–0.820638seconds. These are local fixture measurements, not model cancellation SLAs.
- PID/exit/timing records: owned-pid-metrics.jsonl; each controller SIGKILL record includes controller and worker PID, controller exit-9 and worker termination confirmation.
- Direct leader is reaped by subprocess.wait. For orphaned descendants, /proc missing or zombie state proves non-execution; this controller does not claim it reaped a process adopted by PID1. Detached descendants escaping the process group, hung uninterruptible OS states and production supervision are not proved.
- Existing InvocationGuard remains cooperative. It is not automatically injected into every worker/acceptance/GitHub call. The tester performs stop detection and coordinated termination at explicit boundaries. Actual formal host-agent cancellation and provider coldstart remain unverified; arbitrary code between checks is not preempted.
- Python-only scope: npm/build/browser/production tests are not applicable and not claimed.

The dedicated contents:read CI has a five-minute timeout, no schedule, cancel-in-progress:false, ten bounded lifecycle rounds and seven-day retention for fixture-only PID metrics. It does not install/enable a worker service or reset budgets.

## Protected retained state and restart position

Retained state uses mode=ro only:45total/43implemented/2blocked/running0, original4spec_hash match, logicaldigest281bd3a0b00057eef2a00cdd5d7283d8cc8f4031f39f029c63c5af8533670ada. Checkpoint remains b8afdc9feb93d142f723c41850d5806c0efc5917cafe6cd2324255cdab2555c0. Existing local run_count1/run_limit28 is preserved and is NOT evidence of provider remaining reservations/budget. No task, token, private receipt, raw database or credential is exported; synthetic PID evidence contains no retained context. Old blocked C-chip-oracle-v1 and D-doubleclick-v1 are untouched. New source work is tracked in Git only, not inserted into the retained DB.

Next: review this stack and its exact CI/source hashes; keep PR111 and this candidate Draft. For an actual host-source continuation experiment, require an already-reviewed real task, formal agent liveness/stop integration and an explicitly approved bounded invocation opportunity. Do not reinterpret this fixture chain as independent scheduled development. Controller activation/main merge/new reservation remain separate approvals. PollNO-GO; no Supabase/Vercel/billing/main changes.

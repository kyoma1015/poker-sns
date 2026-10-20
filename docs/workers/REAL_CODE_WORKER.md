# Issue #22 — finite real-code worker adapter

Status: **four real host-session implementations verified; nested CLI remains BLOCKED; no persistent daemon**.
This is a new implementation on top of PR #16, not a claim that unattended development is running.

## What is implemented
`scripts/code_worker.py` connects reviewed task descriptors to the installed Codex CLI, not a fixed code-generation template. Its real executor calls `codex exec --ephemeral --sandbox workspace-write` with network disabled for model-generated commands and a restricted shell environment. No model name/provider is silently substituted.

Four lanes can run concurrently, one reviewed task per lane, maximum four tasks/batch. Every task pins a full source commit, dedicated `codex/` branch, exact writable source paths, immutable acceptance-test paths and an allowlisted test profile. The test profile is fixed controller code, not a shell command embedded in queue data. Protected tests must already exist in the pinned source commit; missing tests block execution rather than weakening acceptance.

Shared SQLite WAL state uses `BEGIN IMMEDIATE` to claim development tasks. One running task per lane, random lease tokens, lease expiry becomes BLOCKED, stale/replayed completion is rejected, immutable IDs cannot change task specification, and at most two explicit attempts are possible. Failed worktrees are retained; no automatic reset, overwrite or lease stealing. A shared filesystem setup lock serializes Git worktree preparation.

The model is instructed to edit only reviewed paths. The controller independently rejects no-op output, out-of-scope/ignored-file changes, deleted/symlinked source, changed HEAD and acceptance-test changes. Test-success source hashes must still match after testing, and staged Git blobs must exactly match the tested version. Git hooks/fsmonitor are disabled on controller commands. Commit is created only after tests and these checks pass.

CLI output is bounded to2MiB and task time to180s (lease includes test/commit time). The finite batch uses at most four threads and exits; there is no daemon or self-rescheduling loop. Output text is discarded after collecting event metadata, and exception summaries redact common bearer/token/JWT formats. Those redactors are defense in depth, not permission to put secrets in model output.

Credential separation: API keys, GitHub token and Supabase service-role keys are not passed to the model's shell environment or test process. Codex uses the existing configured subscription authentication; the adapter does not copy auth, change CODEX_HOME, register secrets, select paid APIs or enable services. A separate runtime attestation must confirm existing ChatGPT subscription and no new paid services before opting in. An attestation is a human/coordinator assertion, not proof that authentication/runtime execution works.

## Publication boundary
Local implementation and publication are separate. Optional `--publish-draft` uses an existing runtime GITHUB_TOKEN in a controller-only API client, checks the exact remote base SHA, refuses any existing remote branch, pushes only a new `codex/` branch using existing Git transport identity, then creates a Draft PR. Tokens are not included in argv, Git config or model/test environments. API failures leave publication BLOCKED. A test-fixture executor is never allowed to publish as real AI output. No merge, deployment, SQL, production DB or billing command exists in this publisher.

`GITHUB_TOKEN` must already be correctly scoped by the runtime. Nothing here provisions or registers a new credential. The managed connector's credentials are not assumed to be available to a child process. A successful push followed by failed PR creation may leave an unmerged branch requiring reconciliation; it is not retried by overwriting the branch.

## Real activation prerequisites
1. Approved existing-subscription CLI identity, working runtime, and no new chargeable API configuration.
2. Reviewed immutable tasks with existing protected acceptance tests.
3. Durable shared SQLite path and work-root accessible by all participating workers; do not use per-run ephemeral CI state as a cross-run lock.
4. Separate review of untrusted-code sandboxing and runner capability. Post-flight path checks alone are not an external security boundary. Model commands rely on Codex's supported sandbox; never bypass it to make the run work.
5. For publication, an existing scoped GitHub runtime credential and transport identity, with branch-only write permissions.

The controller can be run manually from an authorized existing runtime:

`python -B scripts/code_worker.py --manifest /reviewed/tasks.json --repository /clean/repo --work-root /durable/worktrees --state /durable/worker.sqlite --output /durable/run.json --auth-attestation /runtime/subscription-attestation.json --enable-code-writing`

Add `--publish-draft` only after the publication credential/access checks are satisfied. No active manifest is shipped: task instructions and acceptance tests require review before enabling real code writes. The descriptor fields are `id`, `lane`, `base_sha`, `base_branch`, `branch`, `instruction`, `allowed_paths`, `protected_tests`, `test_profile`; repository must be kyoma1015/poker-sns and manifest version1. Test profiles are listed in controller source.

There is no API/token spend limit claim: this adapter refuses API-key billing and relies on an approved existing-subscription runtime, finite tasks and walltime. It does not create a paid account or enable metered usage.

## Evidence and current blockers
- CLI0.159.2 exec help inspected; no bypass flags used.
- Root coordinator's actual CLI startup attempts failed before model execution with `failed to initialize in-process app-server client: Read-only file system (os error 30)`. An allowed log/sqlite-directory override did not fix it. The managed CODEX_HOME was not changed/copied and sandbox was not bypassed.
- A separate sandbox-help call also returned `app-server socket directory must be a user-owned directory with mode0700`. No repeated attempt to bypass the runtime was made.
- Therefore nested-CLI model-generated implementation and standalone publisher/daemon activation remained **BLOCKED/NOT VERIFIED** at that observation. The later approved host-session milestone below is separate and does not erase the CLI failure.
- `python -B tests/automation/test_code_worker.py`:22 tests, including four concurrent test-fixture code writers with real Git worktrees, acceptance tests and commits. They are explicitly `test_fixture`/real_ai_implementation=false; this is not evidence of real Codex model execution.
- Existing `tests/automation/test_development_queue.py`:15 regressions retained. CI executes both suites without model credentials.

After the legitimate runtime capability is restored, execute one reviewed task per lane and inspect the output evidence/commits/CI before declaring a real milestone. Preserve the original source, old worker branches and checkpoints. The infrastructure is still not a persistent daemon; a separately authorized scheduler plus durable state is needed for repeated unattended runs.

## Approved host-session backend
`scripts/host_session_worker.py` adds a second executor lifecycle for an already authorized host that exposes formal collaboration tools. It does not bypass, repair or impersonate nested Codex CLI authentication. It cannot itself create a collaboration agent from a shell.

1. `prepare` pins the source, acquires the same shared development lease, creates the dedicated worktree and stores protected acceptance hashes in coordinator-owned state.
2. The trusted host coordinator dispatches its actual formal collaboration agent to that worktree with the reviewed instruction. Source editing occurs through that host's existing tools/permissions.
3. The coordinator records the actual agent identity in an external receipt and calls `finish`. The controller rechecks source/acceptance/lease/HEAD, runs real fixed tests, verifies tested/staged hashes and creates a commit.

Receipt identity is an assertion of the trusted host coordinator; a shell JSON file is not cryptographic proof of a collaboration identity. Do not accept receipts from task/model output. The coordinator must independently witness dispatch/completion. Preparation alone is not AI execution. Unit fixtures use `test_fixture=true` and can never claim real implementation or publish through the real publisher.

Prepare example: `python -B scripts/host_session_worker.py prepare --manifest /reviewed/tasks.json --task-id TASK --repository /clean/repo --work-root /durable/worktrees --state /durable/worker.sqlite --prepared /coordinator/TASK-lease.json --output /coordinator/TASK-prepared-public.json`.
Finish example: `python -B scripts/host_session_worker.py finish --task-id TASK --state /durable/worker.sqlite --prepared /coordinator/TASK-lease.json --receipt /coordinator/TASK-agent-receipt.json --output /coordinator/TASK-result.json`.

The receipt requires matching `task_id`, `dispatch_source="collaboration"`, `completed=true`, and actual `agent_id` such as `/root/lane_b`. This backend is usable only during a legitimate active host session. It does not provide a persistent scheduler or prove future scheduled sessions have shell/agent/lease capabilities.

## Actual host-session activation milestone
The trusted root coordinator completed a finite four-lane run using this exact lifecycle. This is real project source modification by formal collaboration agents, not the fixture executor:

| Lane | Real defect fixed | Actual agent | Controller-created commit | Draft PR |
|---|---|---|---|---|
| A | Reject malformed poll option counts before vote RPC | /root/host_a | 9bf10fc8de11fd6644876c50439b3e5fc1ffa24d | #27 |
| B | Empty offline question export is REVIEW_REQUIRED | /root/lane_b | a36c7853ca745b40d9607d096b8a2f72c5f5712d | #28 |
| C | Finite mass sum overflow becomes validation ValueError | /root/lane_c | 89fd492422497714d1665a9523e97ad4ba3ebee2 | #29 |
| D | Reject malformed persona answer count/letters in offline audit | /root/lane_d | 6e72672fe1b9e51feb6c5b398dd9d757da83e110 | #30 |

All four immutable acceptance suites failed before source editing. The actual agents changed only reviewed source paths. The controller independently reran five acceptance cases (A1/B1/C2/D1), rechecked source/acceptance hashes and created four commits. Reclaiming the same task IDs returned none for all four tasks, proving no duplicate execution in the retained shared state.

Public evidence is in docs/qa/issue22-workers/host-session-results.json, host-baseline-failures.json, host-session-manifest.json and completed-no-replay.json. Lease tokens, private prepared receipts and SQLite databases were deliberately not copied. The result records publication=not_attempted because that controller stage does not use a GitHub credential; the root coordinator subsequently pushed and created the four Draft PRs using its existing approved GitHub tools. This is evidence for formal host dispatch/source/test/commit and root publication, not evidence that the optional standalone publisher authenticated successfully.

No main merge, production deployment, Supabase call, old checkpoint write, auth copy or new paid service was performed. The CLI EROFS blocker still applies. A single finite host run is not a persistent daemon or proof that the next unattended scheduled session has runtime/collaboration/lease capabilities; that future run must check its capabilities and shared state again.

### GitHub CI and finite scheduler connection
Root-created Draft PRs also passed their immutable-acceptance CI at their published commit:
- A #27: https://github.com/kyoma1015/poker-sns/actions/runs/39513425434
- B #28: https://github.com/kyoma1015/poker-sns/actions/runs/39513431818
- C #29: https://github.com/kyoma1015/poker-sns/actions/runs/39513440363
- D #30: https://github.com/kyoma1015/poker-sns/actions/runs/39513447188

The root coordinator updated the existing finite restart reservation prompt to use the approved host prepare → formal dispatch → finish lifecycle when available. The existing six-hour interval and occurrence limit28 were not expanded or auto-renewed. The update API succeeded, but the next scheduled cold start through actual code completion has **not** been witnessed. The previous managed-runtime CLI failure remains recorded, rather than being hidden by host success.

The retained coordinator lease state is `/workspace/work/issue22-host-controller/leases.sqlite`. Its database and private receipts/tokens were not published. A subsequent session must verify state continuity and absence of conflicting work; missing/unavailable state forces read-only behavior. A path in documentation does not guarantee storage durability across instance replacement.

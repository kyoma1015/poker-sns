# Four-lane execution infrastructure — 2026-10-20

Status: bounded validation infrastructure implemented; unattended code development NOT running.
Base: PR #13, codex/integration-poll-only-20261020 @ 3ca87764e988cac588fef915d48823702a1a3326.
A/B/C/D are being developed concurrently by separate agents/branches during the current Codex session. A session is not a persistent service.

## Implemented and tested
- Independent A/B/C/D queues with immutable task IDs and acceptance criteria in .github/queues/development.json.
- SQLite BEGIN IMMEDIATE transactions, one live lease per lane, duplicate protection across connections.
- Lease expiry becomes BLOCKED; no implicit lease stealing or duplicate work. Other lanes continue.
- Failed validations back off 60/120/240 seconds, max three attempts, then stop. No unbounded retries.
- Fixed allowlisted validation command, subprocess timeout 60 seconds, max four tasks per run. Queue text cannot contain shell commands.
- Development tasks are never marked implemented by a validation result. No code-writing worker, model API, secret or paid service is configured.
- Queue state is persisted locally for resume; CI creates disposable per-job state and evidence artifacts (retained seven days). CI artifacts are not a durable autonomous development-state service.
- GitHub Actions workflow runs four independent validation jobs, max-parallel4, timeout3min each, contents:read, checkout credentials disabled. No PR writes, merges, deployment, DB or issue/email notifications.
- workflow_dispatch and pull_request triggers support verification. Schedule weekdays 03:17 UTC is dormant until the workflow is installed on default branch AND POKERID_VALIDATION_SCHEDULE_ENABLED=true. This would run validation/planning only, not autonomous programming.
- Notifications are limited to GitHub's existing failed-check UI; no external messages sent.

## Reproduce
`python -B tests/automation/test_development_queue.py` — 15 safety tests.
`python -B scripts/run_queue_validation.py --state /tmp/pokerid-queue-new.sqlite --output /tmp/pokerid-queue-evidence` — at most four validations, with logs and JSON report.
`python -B scripts/development_queue.py --state /tmp/pokerid-queue-new.sqlite --lane C` — prints next task descriptors only.
Run again with the same state: completed validations are not rerun. Development descriptors stay queued until a real code worker completes and supplies independently reviewed commit/CI/QA evidence.

## Activation gaps
No default-branch installation or schedule activation performed in this PR. A GitHub schedule on a feature branch is not active. No unattended Codex runner/API credentials configured. New paid AI services or unlimited billing are prohibited. The implemented workflow does not claim to solve this missing worker.
Future integration needs an existing authorized no-new-cost runner, bounded per-task runtime/cost, immutable input commit, filesystem isolation, GitHub branch permissions, release gates and replay-resistant durable state. Never expose repository secrets to untrusted PR code or use pull_request_target to run it.
PR #13 remains unmerged because isolation/privacy/release gates remain unresolved. Do not activate infrastructure by merging #13 wholesale.

## Production access observation
Vercel lists the poker-sns project, but scoped project read/deployment-list calls return403 for the project's owning team. The listing alone does not establish deployment permission. No Vercel CLI fallback is installed in this environment. No production deployment is claimed. No production DB was accessed.

## Bounded ChatGPT restart reservation (separate from GitHub scheduler)
A connected automation was created successfully after a successful GitHub read: interval6h, count28, enabled=true. No existing duplicate was present. The service chose the user's timezone automatically; no workspace-timezone substitution was used.
Actual execution is NOT verified: next_run_time and last_run_time were null on creation. Immediate run verification returned404 NOT_FOUND / Action not found before invocation. Do not report this as a running development worker. No repeated retry or new paid service was used.
The saved prompt bounds work to four small tasks and30min/run, suppresses unchanged notifications, requires GitHub overlap/lease checking, and prohibits production/merge/DB/expense actions while capabilities remain unresolved. If execution/lock/test capabilities are unavailable it must remain read-only and record BLOCKED. The finite schedule does not auto-extend after28 runs.

## Advancing the development queue
The coordinator may call record_implementation with an externally witnessed full commit, repository PR URL and CI run URL. This records implemented, never released. The automatic validation runner cannot invoke it and does not mark development done. Evidence syntax validation is not remote CI verification; the coordinator must independently read GitHub first.
The plan excludes implemented tasks and reveals dependent next tasks only when prerequisites are implemented/succeeded. Missing/cyclic dependencies fail closed. Persisted task specs cannot change under an existing immutable ID.
The CI state is ephemeral; leases/retry counts are not a deployed cross-run distributed lock. A future code worker needs a durable shared store before unattended writes are enabled. The reservation prompt remains read-only if that prerequisite is absent.

## Issue #22 adapter milestone (2026-10-20)
A finite real-Codex adapter, separate development leases, exact-path/test/commit guards and optional Draft publisher are now implemented in scripts/code_worker.py. See docs/workers/REAL_CODE_WORKER.md for the capability contract. 21 worker tests (four parallel fixture writers, not real AI) and15 existing queue tests pass. Actual model startup remains BLOCKED by managed-runtime EROFS/socket setup; no auth copy, API billing or sandbox bypass was attempted. Adapter existence and fixture commits are not evidence that four unattended AI developers are running.

An approved host-session lifecycle (prepare → formal collaboration dispatch → finish) is also implemented. It uses the same durable lease/source/test/commit checks and never impersonates a CLI agent. Actual host-session activation evidence is recorded separately from fixture tests and nested-CLI failure; it is not a daemon. See docs/workers/REAL_CODE_WORKER.md.

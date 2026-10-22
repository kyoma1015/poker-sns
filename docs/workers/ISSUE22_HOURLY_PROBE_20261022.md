# Issue22 approved hourly read-only launch probe

Status: registration CONDITIONAL PASS; independent launch verification PENDING; unattended development OFF.

The owner explicitly approved exactly two hourly read-only observations on 2026-10-22. The original Poker-only six-hour automation configuration was saved in `../qa/issue22-hourly-probe-20261022/previous-automation.json` before pausing it. The update returned success and a separate lookup confirmed disabled. Its next-run-null cause remains UNKNOWN. No other task was changed. Do not restore the old reservation automatically.

The provider create returned success, enabled, exact_schedule, DTSTART 20261022T160246Z and RRULE FREQ=HOURLY;COUNT=2. A separate lookup confirmed this finite configuration. Both next_run_time and run history are null. Therefore the calculated UTC occurrences 16:02:46 and 17:02:46 (JST Oct23 01:02:46 and 02:02:46) are configuration-derived expectations, not delivery evidence. No run_now, manual source worker, replacement scheduler, extension or paid service was used.

Canonical machine record: `../qa/issue22-hourly-probe-20261022/registration.json`. Checkpoint: `RUN_CHECKPOINT_20261022.json`; its exact SHA256 and original four task hashes are recorded in the baseline JSON next to registration. Current main was freshly fetched as 781f038415503ece850c25a26e72ef67dee9c8a1. PR106 and107 remain unmerged Drafts; CI39795238064 and39796232980 are completed/success at their current heads. Prior run39785868353 is also completed/success.

## Each scheduled observation (read only)

1. Fetch current main, PR38 head, this document, registration and saved checkpoint through existing GitHub authentication.
2. Read the registered task with official automation peek. Record actual last_run ID, scheduled/start times, chat_ref type and latest_result matching run ID/time. Null means UNKNOWN; same conversation does not establish an independent Codex coldstart.
3. If shell and the existing shared database exist, open only `file:/workspace/work/issue22-host-controller/leases.sqlite?mode=ro`. Compare original manifest task spec hashes without reading tokens or receipts. Count statuses and check running jobs. Never create replacement state or acquire a lease.
4. Compute checkpoint SHA256 and identify its Git commit. Compare baseline; for the second run compare the official stored first observation, if accessible. Never invent cross-run progress from the static checkpoint alone.
5. Report capabilities, same-host/coldstart evidence, overlap observations, errors and remaining blockers in one self-contained Japanese code block. The provider result is the only permitted new observation store during this read-only probe. No source, SQLite, GitHub or scheduler writes.

## Limits and stop

Exactly two provider occurrences; no automatic restore/extension or continuous development authorization. A transient read may retry once; repeated authentication errors stop. Missing state, unknown liveness or missing formal tools are BLOCKED. No CLI/HOME/auth bypass, production access, Vercel, merge, billing or poll release. Account-level cost telemetry is unavailable; no new paid integration was introduced.

## Acceptance still outstanding

Two actual provider runs, explicit IDs and launch evidence, preserved checkpoint and original state, no duplicated tasks, and visible prior observation inheritance. A read-only observation cannot prove the live source-worker guard, emergency stop, rate-limit recovery or successful automated implementation. Even two successful observations do not authorize ongoing source development. After results, owner must separately approve operational cadence/count/budget, a verified execution backend and any controller adoption; keep all existing production prohibitions.

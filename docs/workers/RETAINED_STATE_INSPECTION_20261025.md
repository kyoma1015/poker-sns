# Read-only continuity inspection, not execution or startup permission

`scripts/inspect_retained_state.py` packages the existing coordinator manual probe from `/workspace/work/issue22-readonly-continuity-20261024.py`. It does not create a controller, queue, lease, database, schedule, run, receipt or task. No network request or automatic retry occurs. A successful match always reports `execution_allowed:false` and `automatic_startup:UNKNOWN`.

Inputs are four explicitly supplied trusted local paths: `--state`, `--manifest`, `--checkpoint`, `--expected`. The expected file uses the existing public observation shape: `total`, `counts`, `full_rows_digest`, `run_count`, `run_limit`, `original4`, `checkpoint_sha256`; optional historical timestamp is ignored. The manifest contains four distinct task objects in the existing `tasks` list. Preserve trusted expectations separately from the database under inspection; this tool does not authenticate their origin or make stale expectations fresh.

The database must already exist as a regular non-symlink file. A `file:` URI with `mode=ro`, query_only and one read transaction reads the existing eight-column development_jobs schema, continuation_runs and continuation_limits. No DDL, table repair, claim, activation or writes are issued. WAL is observed normally: `immutable=1` is deliberately not used because it can ignore committed WAL. Standard SQLite WAL read-side locking still applies; this is not a guarantee that SQLite never touches shared-memory bookkeeping. Database content and WAL bytes are checked unchanged in owned tests.

Whole-row digest is exactly SHA256(json.dumps(rows,sort_keys=True).encode()) on `SELECT * ... ORDER BY id`, matching the manual probe. Task digests use SHA256(json.dumps(task,sort_keys=True).encode()). Raw rows, evidence, tokens and SQLite bytes remain in process memory and are never returned. Output contains only public counts/digests and original task ID/match/status. All errors are fixed reason codes without raw SQL errors or input paths. JSON rejects duplicate keys, NaN/Infinity/overflow, invalid UTF8 and malformed expectations. Input artifacts are limited to8MiB, rows to10000 and SQLite busy timeout to1s; kernel/filesystem stalls and hostile trusted-input mutation are not hard wall-clock guarantees.

Example (trusted private paths are placeholders):

```
python -B scripts/inspect_retained_state.py --state STATE --manifest MANIFEST --checkpoint CHECKPOINT --expected EXPECTED
```

Exit0 means continuity match only. Exit2 means BLOCKED and no execution permission. Missing state is not created. It does not prove worker liveness, provider startup, complete PR/CI freshness, authorization, safety of all stored field values or automatic resumption. A future separately approved host can invoke this before existing continuation logic; merely installing this script does not connect or start that host.

Fixed new-contract baseline:12 ModuleNotFoundError before implementation, not12 existing product failures. After implementation12 tests PASS/0FAIL. Tests use only owned temporary SQLite, real subprocess CLI, WAL snapshots, schema/missing/corrupt cases, private field tampering, original task hash and budget/checkpoint mismatches, strict JSON and sanitized error output. The valid observation is compared to an independently implemented copy of the prior manual algorithm. Actual retained state is reserved for root's read-only observation; this agent and test suite did not open it.

Evidence: `docs/qa/retained-inspection-20261025/{before.txt,after.txt,RESULT.json}`. No npm build needed for these Python-only files. Existing broader suites and GitHub CI are the root coordinator's responsibility;12 local tests alone are not CI success or AUTO-RESUME ON. No main merge, PR, workflow dispatch, production, billing, host/controller or scheduler activation occurs here.

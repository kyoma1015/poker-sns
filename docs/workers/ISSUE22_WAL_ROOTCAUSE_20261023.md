# Issue22 WAL initialization race — exact existing fix inherited by audit Draft

Explicit manual task began2026-10-22T17:05:41UTC (Oct23 02:05:41JST). No scheduler/controller/main/production activation is performed.

## Root cause and original failure

PR38 headcc495c914284d955e0d6b75be55818bdd8081f54 still contained the complete pre-PR69 code_worker.py blob e45d66a236c407b458fb780db9fa199b5111b895. Its Leases constructor opened SQLite and issued journal_mode=WAL before participating in the existing cross-process setup lock. Multiple fresh initializers could race at that pragma despite connect(timeout=10); setting busy_timeout later did not serialize bootstrap. A DDL/pragma exception also left the newly opened connection unclosed.

AuditCI39817880993 attempt1/job119961040154 failed test_four_real_git_worktrees_and_commits_without_faking_ai with sqlite3.OperationalError:database is locked at journal_mode=WAL. Attempt2 passed after a single failed-job-only retry; that was not a fix. Exact retained PR69 regression tests on immutable audit inputa18885d839ffee6b06bc0b456c85c968a9e2efe6 reproduce27tests/2FAIL: setup exclusion bypass and connection cleanup failure. No fabricated failure or old completed task replay.

## Selected reuse, not a second implementation

Existing PR69 source4d30c7ac0d08104f9d159987e38c823ef7c3b419 is reused byte-for-byte. Formal integration task issue22-a-audit-wal-reuse-v1 acquires its own lease/worktree. Agent applies only the original patch; host independently verifies protected tests/hash/scope/commit. Source199d15d7f0302ffaeb27185ae50ceb1ad634ea1e changes code_worker.py (+13/-8), with exact original patch bytes and target SHA25637a539e207c46ee5ad94bdf6c877cf835e5188a217169ed1f5aa2885ce0def15. New algorithm count is zero; this is one integration task.

Manual overlap review covers the fresh complete63openPR files/base/head snapshot. PR69/74/80/85 constructors match the selected initializer AST; PR26 is the older baseline. Only the audit Draft is updated, no other PR/branch is retargeted or merged. This manually authorized selected-reuse review is not a claim that the automatic candidate planner approved new unknown overlaps, and its gates/code are not weakened.

Order: setup_lock(state) → connect(timeout10s) → WAL/busy_timeout10000/schema → release setup lock. On initialization exception: close connection → release setup lock → propagate failure. Claim transactions occur after constructor release; prepare's later Git setup lock is a separate section, so this path does not nest the same setup lock. Bounded setup wait remains30s. This does not promise arbitrary non-cooperating external DB writers cannot fail after their timeout.

## Executed isolated verification

- Fixed27PASS, worker22PASS, queue15PASS.
- Initialization3tests and worker22tests each repeated10times: all PASS.
- Eight independent processes released from a shared start barrier against a fresh owned SQLite,10generations:80successful initializers, all8rows retained per generation, journal_modeWAL and integrity_checkok. No retained/user DB path is accepted by the harness.
- Existing failure injection confirms connection close, guard release and subsequent restart. Existing cross-process guard test confirms DB is not opened while another process owns setup lock.
- New bounded stress harness and repeated suites added to existing PR CI (contents:read,5min cap), no cron/new service/model invocation. These are synthetic fixture/process tests, not real AI daemon or production DB tests.

## Runtime boundary and state

Audit Draft code is corrected; the retained active controller checkout is NOT switched. The more complete pinned controller candidate6d2f4834d3a06abb61058fcebca952f360ec0f45 already contains serialized initialization and exact PR106 continuation checkpoint source; it remains unadopted pending explicit activation approval and execution gates.

Existing43task records/BLOCKED history are retained. One new selected-reuse integration row gives44total/42implemented/2blocked/running0 after completion; counts include integration work, not42new algorithms. OldC-chip-oracle-v1 remains blocked due wrong scalar refund oracle, superseded by v2/PR66; oldD-doubleclick-v1 remains blocked due dependency/cache scope violations, superseded by v2/PR35. Do not retry or rewrite their immutable histories. Independent reconstruction of two older integration descriptors remains UNKNOWN; original4 anchors match.

## Automatic launch evidence remains separate

Both reservations are disabled; no registration/resume/extension occurred. Saved and current schedules match. Probe DTSTART16:02:46UTC plusHOURLY COUNT2 implies second17:02:46UTC; recorded last_run_time16:57:54.154987UTC is291.845013seconds early. Converting America/Los_Angeles and JST consistently leaves the same difference, so timezone conversion alone does not explain it. Only latestupdated_at16:57:54.396998UTC is exposed, not actor/change history. last_run.id/scheduled_for/started_at/completed_at/chat_ref/latest_result are null, so dispatch/clock/history causes and normal COUNT2 completion remain UNKNOWN. Prompt arrival/read-only checkpoint success do not prove independent Codex startup or automated source processing.

Current checkpoint advances belong to explicitly authorized manual work. Existing read-only probes cannot acquire task leases/start workers/write state by design. Independent backend/runID/continuity/global guard/stop/usage-budget evidence remains required before unattended operation. No productionSupabase/Vercel/main merge/billing/pollrelease; pollNO-GO.

Evidence: docs/qa/issue22-wal-rootcause-20261023/. Next: verify new audit CI at actual head, then keep completed integration ID immutable; review any controller adoption separately. Continue independent safe development only with a grounded new task, protected acceptance and current overlap/lease evidence.

## Completed follow-up at 2026-10-22T17:26:50.455326+00:00

A audit head885ea6823f1903ac316d5fafffeb3a0213e5fd0d CI39821508379 SUCCESS, including repeated suites and80process initializers. C existing main-target PR103 lacked PR108/110 source: protected immutable input2c24d4f195da3bce4b228a413cfee6165c1998df reproduces33tests/10ERROR. Exact latest source dd883b7ded3b792b366c12b18e3b1937ca469156 reused by formal integration task issue22-c-hand169-followup-reuse-v1; commit a4f93af20d5ff85371ecb61c347aaf7df23a68cf, fixed33PASS plus old10PASS, Actions39822187456 SUCCESS. No new algorithm or old completed task replay. Latest state45total/43implemented/2blocked/running0; original43records preserved. Evidence C-followup/. Both changes remain Drafts, main unchanged. B350 official provenance and D36animal expert labels remain unverified; G11 ABI/checkpoint and actual strategy convergence remain unproven. No controller/scheduler adoption.

# SQLite initialization exclusion and cleanup — before source

CI39712373480 attempt1 observed simultaneous Leases constructors fail at
PRAGMA journal_mode=WAL with database locked; attempt2 passed without code fix.
Leases currently initializes journal/schema before acquiring any setup exclusion.
The existing bounded cross-process setup_lock only wraps later Git preparation.

Acceptance: an independent initializer must respect that existing setup exclusion
before opening/migrating state;8 real fresh concurrent initializers must retain
WAL/schema/all rows; schema initialization failure must close its connection and
release the guard. Existing lease/replay/expiry/hash/tamper/acceptance behavior is
unchanged. Do not add unbounded retries, steal leases, weaken tests or use live
private leases.sqlite in tests. All DB files are owned temp fixtures.

Only scripts/code_worker.py may change. Use the existing bounded setup primitive
for initialization and clean up failed connections; do not alter claim/finish,
allowed paths, protected hashes, executor/publication or retry policy. Root will
review the actual diff and run existing22 worker,15 queue and recovery tests.
This is an independent A/infrastructure Draft, not a merge into PR38 or main.

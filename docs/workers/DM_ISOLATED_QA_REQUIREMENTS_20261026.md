# Authentic DM isolated verification receipt requirements

Status BLOCKED, not a schema implementation. Read-only search across all77 pinned open-PR heads found no direct_messages reference in tracked SQL. Current checkout has no psql/initdb and no approved isolated DB endpoint; production is forbidden. No SQL was executed and no original schema has been reconstructed by guesswork.

To make the existing client tests into authentic integration QA, obtain a reviewed, sanitized schema-only artifact with origin commit/date/SHA256: direct_messages and user_blocks columns/defaults/constraints/indexes; grants/default privileges; all SELECT/INSERT/UPDATE/DELETE policies and helper functions/security context; notification/event hooks if applicable; relevant authenticated/anonymous role and auth.uid semantics. No user rows, credentials, JWTs, real backups or production secrets belong in the artifact. Identify the schema owner and environment isolation before running anything.

Use disposable local identities A/B/third-party and a new isolated database/storage project with confirmed no production sharing. Seed only synthetic rows. The executable acceptance must cover:

1. A→B send and both-party read; C/anonymous cannot read or write it.
2. Forged sender/receiver, arbitrary UPDATE/DELETE, author reassignment and direct REST/RPC/legacy-client paths fail.
3. A blocks B and B blocks A; read/send behavior matches the formally approved block contract (not invented from current UI).
4. Auth error/expired identity/account switch cannot mark/read another account; returned-user-plus-error fails closed.
5. Identical client operation/network ambiguity/retries and multiple tabs do not duplicate accepted server operations; current client lock is not a server idempotency proof.
6. Read acknowledgement owner predicate, zero-row policy denial, concurrent updates, realtime account isolation, notifications and cleanup.
7. Failed transaction rollback, no prior committed synthetic data loss, finite timeout, rerun with unique test namespace, disposal confined to this isolated environment.

Record role/auth state, sanitized request/result, fixture hash, affected row counts and before/after digests. Backend write/role tests remain unexecuted until this receipt and an authorized disposable environment exist. Do not connect production or expand permissions to bypass this gate.

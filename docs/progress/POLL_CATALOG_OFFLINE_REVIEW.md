# Offline poll catalog review — 2026-10-21

This tool adds no database connection, SQL execution, schema or access grant.
It reviews only an explicitly supplied local metadata JSON export. It cannot
prove production parity or approve deployment. Existing poll PR31 isolated DB
acceptance remains 56PASS/0FAIL; that synthetic result does not become a real
production catalog check by passing this offline tool.

## Local use and input

`python -B scripts/poll_catalog_review.py isolated-catalog.json`

Prepare a metadata-only object with exactly `version: 1` and arrays `columns`,
`functions`, `policies`, `grants`, `cron_jobs`. The first four sections use the
existing `sql/poll_only/preflight_readonly.sql` result sets from an explicitly
authorized isolated/staging environment. No production query is authorized by
this document. The existing SQL is not a complete export command: cron inventory
is still a separately authorized, reviewed collection step. Do not include user
rows, credentials, connection strings or Auth tokens. Do not assume defaults or
function text have no sensitive information; retain exports privately and share
only the fixed reason-code report after review.

Column keys: relname, relrowsecurity, attname, type, attnotnull,
default_expression. Function keys: signature, prosecdef, proacl, definition_hash.
The signatures and MD5 definition hashes are catalog metadata, not proof that
function bodies implement safe logic. No row data or default expression is
executed or echoed. Policy/grant/cron rows are accepted as metadata dictionaries
but their semantics deliberately remain an owner/security review gate.

The CLI rejects duplicate JSON keys, malformed JSON, read failures and files
over4MiB using fixed codes. It does not expose the source path or parser failure
details. The pure `review_catalog` API never mutates its input.

## What is checked

- Six required app tables and referenced column types matching the candidate.
- Notification RLS enabled; absent or ambiguous inventory fails closed.
- Recognized historical create/read/response RPC signatures; unknown overloads
  require review rather than overwrite.
- Required columns omitted by candidate INSERTs need defaults or nullability.
- Missing explicit privacy-column metadata cannot infer old poll modes.
- Duplicate/malformed metadata cannot silently replace earlier rows.

A structural mismatch reports BLOCKED and CLI exit2. Even a structurally matching
inventory reports REVIEW_REQUIRED and CLI exit3, with production_approved=false,
db_connected=false and POLICY_GRANT_CRON_REVIEW_REQUIRED. There is no PASS or
override flag. Conservative type/signature mismatches must be reviewed against
the exact authorized schema, not massaged to make a test green.

## Remaining release gates

Actual authorized staging/catalog and historical privacy mapping are absent.
Real policy/ACL/cron/function-body semantics, additional constraints/triggers,
GoTrue login/refresh, real-DB UI, normal migration history/advisors, and approved
SQL/backup/full schema/ACL restoration remain unfinished. Existing feature-disable
SQL is a data-preserving stop, not complete schema restoration. Vercel403 scope
must be resolved through legitimate access; no bypass or deployment is performed.
Historical questions/answers, original artifacts and existing SQL remain intact.

Fixed acceptance is protected under tests/worker_acceptance/test_poll_catalog_review.py.
The fixture is synthetic. Host controller must rerun these ten contracts and
verify source/protected hashes before producing the implementation commit.

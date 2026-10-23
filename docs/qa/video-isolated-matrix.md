# Short video QA matrix (PR #123, isolated candidate)

This is a static contract test, NOT an isolated Supabase end-to-end test.
Run `node --test tests/video-isolated-contract.test.mjs` in CI.

| Test | Static coverage | Live isolated DB/Storage coverage |
| --- | --- | --- |
| posts.video_path schema | SQL presence | NOT RUN |
| Private Storage and 20MiB limit | SQL presence | NOT RUN |
| Owner INSERT/SELECT/DELETE RLS | Policy text | NOT RUN |
| Non-owner read blocked | Policy text | NOT RUN |
| Authorized non-owner read | BLOCKED: no viewer policy | NOT RUN |
| Signed URL and 300-second expiry | API call presence | NOT RUN |
| 30-second video duration | Browser metadata only | BLOCKED: no trusted server validation |
| Failed post cleanup | Not connected to publication | NOT RUN |
| Delete cleanup | Code path presence | NOT RUN |
| Full video publication | Explicitly disabled | NOT RUN |

**Gate:** Keep publication disabled until isolated Postgres/PostgREST/Storage tests actually pass, including unauthorized viewer denial, blocked-user denial, server-side duration rejection and failure cleanup.

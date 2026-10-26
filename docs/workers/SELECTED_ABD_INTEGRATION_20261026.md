# Selected A/B/D integration — 2026-10-26

Latest user instruction authorizes a main-based isolated branch and Draft PR. This supersedes the old batch's no-new-PR gate only for this reviewed candidate. No main merge or production release is authorized.

This candidate selects B → D → A source/test closures from already published exact-head-CI-successful commits. It excludes old Timeline/poll/config/controller histories and all GTO work after exclusive transfer. PR119/121/124 and original histories remain unchanged. No C files or PR120 updates.

Pinned origins:
- B 8fc0dc9fb1ecbe95d465a005ba2c6a78b9947ada
- D 73baccf20ac770ad28dd52cdf9aa4125542e0ccd
- A 99587abe0aa98a16e3db2c5cf609b1c265a876b8
- main 781f038415503ece850c25a26e72ef67dee9c8a1

source-manifest.json records each exact blob. The read-only verifier rejects unreviewed diff paths and confirms main package/lock, App/Timeline/PostDetail, SQL/poll fixtures/workflows retain their bytes. Browser tests are moved into tests/selected with resource-root adjustments only; assertions are mechanically compared to original pinned Git source. B's misnamed worker-acceptance.test.mjs is actually16 TDA browser cases, retained as tda-rule-search.test.mjs without importing controller code.

Selected coverage:300 pure unit methods and81 child node methods (including wrappers for9 account and8 save browser cases). Equivalent original381 methods and93 actual synthetic-transport browser cases; outer8 launcher methods are orchestration, not additional feature evidence. No official TDA question/classifier validity or real DB authorization is inferred.

Local workspace ENOSPC prevented shell startup before this candidate was assembled. Original new A PlayerSearch and D payload WIP/tests remain uncommitted in their isolated worktrees; neither is silently included. Candidate source comes from already published reviewed snapshots. Remote CI is required and must be matched to final HEAD. GitHub API tree assembly is not local validation. Existing main poll release CI is preserved and can independently run its isolated database checks; those checks do not verify DM or diagnosis RLS.

Unfinished gates: formal DM schema/RLS/server idempotency; official350 immutable input/key/original/translation/reviewer evidence; diagnosis classifier/threshold/ties/expert labels; physical-device and broader SNS cross-feature QA. Existing question-box creation remains retired, old data retained, poll release NO-GO. AUTO-RESUME OFF, independent startup UNKNOWN. Held45/43implemented/2blocked/running0 and original run limit are not changed.

Disk recovery must use only generated dependencies/cache through supported environment tools; no sandbox/auth bypass or artifact deletion. Continue uncommitted A/D work after capacity is restored and run complete final regressions before publishing them. GTO WIP is preserved for its new owner, never integrated here.

# Notification account/read/realtime flow

Before source ca29d209ab960454eba46cf4df2365fca32098f3. Completion contract: remove private notifications on signout/account switch; reject delayed old profile/snapshot; refuse writes if fresh identity fails; scope read acknowledgement to owner; do not treat zero updated rows as success; offer generic retry after failure; support account-filtered realtime and preserve post navigation.

Fixed seven actual React/mobile Chromium cases use synthetic data/transport and block external requests. Before/after are saved in before.txt/after.txt; final test counts and full commands are in runs.json. This is not authentic RLS or production QA.

The source adds synchronous auth invalidation, keyed account content, per-load generations, scoped realtime lifecycle, owner conditions on SELECT and UPDATE, fresh identity before marking read, returned-row confirmation, and redacted read/acknowledgement recovery. Existing poll_closed display/navigation is preserved. No notification creation logic/RPC/schema/policy changes; client conditions never replace RLS. Already-dispatched writes cannot be recalled on account changes. UPDATE returning zero may be concurrent acknowledgement or policy denial; the UI conservatively offers reload.

Full local regressions:123 frontend methods,154 automation+85 protected worker methods, build/lintPASS. Warnings retained. Exact-head CI must be checked after publication.

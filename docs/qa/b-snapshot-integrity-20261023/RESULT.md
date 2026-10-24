# B offline snapshot integrity — interrupted work resumed 2026-10-24

Base PR119 `5024d9000edf49e667ef6cd7ae0c2682ef587da0` is preserved. Source implementation `cf130fdef4691703137f5f088220d139976696d8` and test-only input `5ca250fbb958255f40d7785d88273a005d9f3446` were already committed before interruption. Resume found a clean worktree; no implementation was rewritten or discarded.

New offline CLI joins explicit byte SHA-256 ledger, positive expected question/option counts, fatal UTF-8/JSON parsing and the existing question/answer-key audit. Invalid/mismatched inputs return fixed reason codes without parser fragments or file paths. Exact matching bytes are marked `HASH_MATCH_NOT_PROVENANCE`; official accuracy remains `UNVERIFIED` and publication false even on structural PASS. Input JSON bytes are unchanged.

The ledger is caller-supplied evidence, not an authenticated official source or proof of provenance. Buffer acceptance is capped at5MiB; synchronous read itself remains OS/caller controlled, so this is not a hard allocation/read deadline claim. No UI, RPC, grading, production connection or DB source changes.

Fixed26 cases: absent API caused26FAIL on test input; source implementation26PASS before interruption. Test SHA256 `d49c8977ca4e9cb61fd41bfaf59094ef0af483067898234b68275ae9767bc2b1` is unchanged. Source and fixed baseline were retained, not reimplemented.

Resume npmci initially failed because managed runtime `/home/agent/.npm/_cacache` was unavailable. One corrected install with an isolated `/tmp/issue22-b-snapshot-npm-cache` succeeded. HOME/credentials were not moved or copied. An incomplete-dependency regression was stopped on its own nonzero exit; logs are preserved separately. The subsequent full dependency/test/build/lint results are in the sibling logs. CI exact-head evidence is recorded in the PR body after observation.

Commands:
- `npm ci --cache /tmp/issue22-b-snapshot-npm-cache`
- `for test_file in tests/*.test.mjs; do node "$test_file"; done`
- `npm run build`
- `npm run lint`
- Example on fresh local approved exports: `node scripts/tda-snapshot-audit.mjs questions.json answer-keys.json manifest.json`

Official immutable350/1400 export, official versioned TDA text and per-clause review remain BLOCKED. Earlier scoped main/handoff source search is retained at `../b-answer-conflict-20261023/source-search.json`; no receipt of new official material was observed. Synthetic fixtures here are not published/official350 verification. This work does not declare ambiguity candidates correct or authorize question publication.

No retained SQLite/job/lease/reservation, oldBLOCKED state, main, controller, Vercel, Supabase or billing operation. Separate-owner PR122/123 were not changed. Next: receive an immutable approved real corpus/key ledger, run this CLI, then conduct official clause review with original evidence; hash matching alone cannot establish rule accuracy.

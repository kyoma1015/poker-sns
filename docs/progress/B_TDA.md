# B | TDA isolated main-based candidate
2026-10-20 JST. Branch codex/b-tda-rpc-isolated-release-20261020, base main f8890b6ec11d30676c55dc7dc8801f1da8549d28.
TDA question payload validation, caught RPC transport errors and offline count/duplicate-candidate audit implemented independently of unmerged PR13. Extra sources from PR13 were not imported. Main's existing inline auth logic is preserved; PR11's auth transport correction remains separate.
17 unit tests,5 mocked real mobile Chromium tests, locked install/build/lint PASS. Evidence and release limitations: docs/qa/b-tda-isolated-release-20261020/RESULT.md.
No live DB/auth/SQL or production operations. Published350/official-source comparison remains UNKNOWN; no question publication approved. Runtime RPC/auth integration and existing production high dependency issues remain release gates.

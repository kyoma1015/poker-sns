# Poker ID — Codex handoff evidence transfer (2026-10-20)

## Status: PARTIAL / NOT COMPLETE
This branch is a **handoff staging branch only**; no merge, deployment, or Supabase mutation is approved.

The seven source ZIPs were present and locally read from the conversation runtime. Their byte counts and SHA-256 hashes were measured directly and are in `SOURCE_ARCHIVE_SHA256_20261020.csv`. **The original ZIP binaries have NOT been uploaded to GitHub or Codex**; do not treat the ledger as delivery of their contents.

Source branch: `chore/autonomous-dev-foundation-20261020` (draft PR #8; NOT merged).

### Existing source and evidence already in GitHub (verify by SHA)
- A/F03 selective code branch `test/f03-isolated-integration-20261020`, formerly observed at `cb31df80...`; older broad branch `fix/p0-security-audit-20261018` is not a safe replacement.
- B/TDA PR #6 and #7 previously merged to main; user ZIPs contain QA and SQL records not fully mirrored in this branch.
- C/GTO: G11/G12 source and trials reside in an **untransferred** large ZIP, not in this branch. G12 restart remains BLOCKED until actual source is accessible and rebuilt.
- D: proposed code `fix/player-type-audit-phase1-20261019` / PR #5 and `fix/player-type-qa-phase1-20261019`; reference SHA `d494b058...` needs current branch verification.

### Do not
- Do not run historical SQL scripts as migrations. Their current production application state is not fully known.
- Do not merge this branch or any draft PR, change production Supabase, or deploy.
- Do not mark original ZIP SHA as verified **in Codex** without downloading the actual ZIP and hashing it there.
- Do not equate previous test reports with independent reproduction.

### Next steps
1. Read this README, archive manifest, `CODEX_RESUME.md`, existing `docs/progress/*`.
2. Verify branch SHA and relevant PR states read-only.
3. Continue A/B/D source inspection from existing code branches only.
4. Keep C/GTO blocked until the source itself has been transferred by a supported permanent storage route.
5. Once files are actually transferred, record destination link, SHA-256 from the recipient, and reproduction result; do not simply change `github_uploaded` to true based on the sender hash.

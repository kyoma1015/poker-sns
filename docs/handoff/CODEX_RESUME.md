# Codex resume protocol

## TASK 00H: verify accessible handoff branch (read-only)
1. Check repo and exact branch `chore/codex-handoff-artifacts-20261020`, and `git rev-parse HEAD`.
2. Read `docs/handoff/SOURCE_ARCHIVE_SHA256_20261020.csv` and `docs/handoff/README.md`.
3. Report whether Codex itself has access to the **original 7 ZIP bytes**. Merely reading this GitHub CSV is not sufficient evidence.
4. Audit A/B/D in referenced existing code branches; separate implementation, tests, prod-applied SQL, and missing QA.
5. Do not claim G12 is resumed without actual GTO source ZIP.
6. Keep all changes on isolated branch; no production DB, deployment, merge, new features, or paid services.

## Pending owner handoff decision
Large binary ZIPs (~301 MB GTO, ~209 MB TDA, ~206 MB A) require a secure external storage or release-artifact mechanism supporting Codex downloads. Do not attempt to commit these to ordinary Git history.

## Known audit facts at transfer
- Last Codex audit: main `f8890b6...`; #1/#3/#6/#7 merged; #2/#4/#5/#8 open/draft.
- F03 verified RPC exists but authenticated direct INSERT is still present: release blocked.
- B TDA: 350 public questions and 1400 options in last read-only DB audit, correctness against official rule texts unknown.
- D latest SHA post-update real browser QA incomplete, L01 DB state unknown.
- GTO archive was found and hashed in sender runtime, but receiver has not read it.

## Completion criteria
A series moves to PASS only with reproducible source visibility, SHA comparisons, independently verified tests, and a clear SQL/deployment status. Keep a separate evidence log per SHA.

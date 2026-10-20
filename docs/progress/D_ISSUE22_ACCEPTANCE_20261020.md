# D Issue22 acceptance — before source edits
Base: PR #18, 9051047cfe30bb2a38bb80c8985c0e7ad16e470c.
Defect: audit-player-type builds a Map directly from option score rows. Duplicate option_id rows silently overwrite each other, so a corrupt score export can still report CONDITIONAL PASS. Orphan score rows are also not checked.
Acceptance: duplicate/orphan score rows must produce FAIL; ordinary fixture remains CONDITIONAL PASS (not semantic validation); errors cannot be bypassed by equal duplicated values. Test through injectable in-memory fixtures without editing stored question/score assets. No scoring/SQL/production changes.
Shared path ownership: scripts/audit-player-type.mjs, one new audit test file, D docs and evidence only. No application TSX changes needed.

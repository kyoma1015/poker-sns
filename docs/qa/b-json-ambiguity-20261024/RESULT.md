# B strict snapshot JSON — 2026-10-24

Existing branch `codex/b-snapshot-integrity-audit-20261023` continues exact saved
HEADec826a8. No existing implementation/previous fixed test was rewritten.

A real offline defect was reproduced: JSON.parse silently accepts duplicate object
members with last value winning. The exact-byte SHA ledger could match such an
ambiguous snapshot while the CLI reported STRUCTURE_PASS. Immutable input963a99f:
16methods,14FAIL/2PASS. Examples include duplicate manifestversion/hash/count,
escaped-name alias, questiontext/ID/optionID, correctanswer/explanation/references,
1e999/-1e999 and excessive depth. No parser fragment/private text is printed.

Source0232a9a adds a separate strict decoder and wires it only into the offline
snapshot CLI. JSON.parse still validates syntax; a bounded-depth second pass
rejects decoded duplicate keys and nonfinite numeric results. Keys are local to
each object; normal string escaping and repeated keys in distinct objects remain
valid. Accepted value nesting depth is128 (root depth0); this is an acceptance bound, not a promise that
JSON.parse/readFile has bounded allocation or a hard operating-system timeout.
Input bytes/hash calculation remain untouched. Existing fixed public error codes
are retained. No UI/RPC/grading changes and no answer publication route.

After:16PASS, inherited snapshot26PASS. Full local regression237PASS/0FAIL in13suites (previous221+new16); npmci/build/lint all exited0. Evidence
is recorded in this directory. npmci uses the already approved
isolated cache path without HOME/credential relocation. No PR, CI execution,
production/DB/controller/retainedstate/lease/scheduler/main/billing operation.
The existing workflow definition only gains helper/test path filters; it is not
activated. New PRs remain prohibited by the current explicit instruction.

Official corpus/text/translation/clause evidence remainsBLOCKED. See
SOURCE_RECEIPT_REQUIREMENTS.md for the concrete receipt/review contract and
resume command. Hash/strict parsing success does not prove official correctness.

# D historical persona reference integrity — 2026-10-23

Base PR114: 69472d70be3dcea70fcaffaf301b2d4e32fb672a. Existing PR30/82/100/114 functionality reused, no double application. New fixed13 input tests reproduce12FAIL/1PASS: missing report and incorrect historical raw-score references silently pass the audit. Final13PASS plus prior53+5+6PASS, total77. No protected test, source fixture, scoring, UI or DB change.

The historical30personas carry32rawscore references each. All960 values match recomputation from exactly one valid option per each of50 questions. This is consistency with a checked-in historical calculation, not independent expert validation, not a live diagnosis execution, and not36animal classification. The reference audit rejects missing/malformed raw objects, missing/extra dimensions, inherited dimensions, nonfinite/non-number values and numeric mismatch. Any error suppresses downstream score-distribution evidence.

Classifier discovery: currentbasePR114, original fixture source commit88cbf26b6f839914a9f867868f03b4d77a991ce3, historical fix/player-type-audit-phase1-20261019 and fix/player-type-qa-phase1-20261019, and chore/codex-handoff-artifacts-20261020 were inspected by Git tree. These contain UI/question/presentation fixtures and poker-card SQL, but no formal36-animal classifier function/threshold/tie-break definition. Current UI invokes complete_player_type_v2_diagnosis; inspecting that literal is not an RPC execution or proof of its deployed function body. No Supabase connection was made.

The handoff CSV lists HANDOFF_PACKAGE 2.zip (8,114,065bytes, SHA256508919d59ecda9ff397c76d84011f3c68dbfc6af52abe43b11be6908ac4f2a94) and HANDOFF_PACKAGE 8.zip (2,483,188bytes,SHA2567cfbc0a527c997a8293c92b1fee920101644981353774cdae9f170f9390b654d) as D materials. Their actual ZIP bytes were not found in the bounded local search, so their contents and whether they carry classifier definitions remainUNKNOWN. A CSV is not source receipt.

BLOCKED: actual36-animal mapping, reachability, 1000-profile animal frequencies, boundaries/ties and meaning need authoritative versioned function source/tables and expert labels. The32rawaxes include deception,exploit,balance_awareness etc.; textual mention or score consistency is not proof of correct polarize/range-vs-hand/exploit/balanced-strategy meaning. No strategic scoring specification is invented.

No production DB, Vercel, retained SQLite/job/lease, reservation, controller, paid service or main merge operations. PollNO-GO; independent provider launchUNKNOWN; unattended developmentOFF.

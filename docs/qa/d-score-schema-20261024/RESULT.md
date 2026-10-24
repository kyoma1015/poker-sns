# D score-row schema — 2026-10-24

Existing PR124/base de818958b47f9e3bf8bde0fc16c9dec4045dc00c retained.

Fixed input efd11fc: seven new tests,1PASS/6FAIL. Four malformed shapes were
accepted as conditionalPASS (inherited dimension, inherited option join key,
unknown extra field, array decorated as score object), null row crashed, and an
existing string-scoreFAIL lacked the new schema diagnostic. These are not six
previously published wrong diagnosis results. After source9892469:7PASS.

The offline historical export contract is option_id plus the exact32 own finite
numeric dimensions in traitPositiveMax. Unexpected metadata/axis names require
explicit schema review instead of silent ignoring. Invalid rows produce a generic
INVALID_SCORE_ROW_SCHEMA with row index, and all distribution/strategy evidence
is suppressed. This changes neither scores nor diagnosis semantics, app UI/RPC,
animal classification, DB or source fixture.

Local new7 + existing53/5/6/14/6 =91PASS/0FAIL. npm ci/build/lint succeeded;
pre-existing lint/bundle warnings retained. Existing fixture/tests/scoring/display
source nine files match original base bytes, hashes in protected.json. Historical
50questions/222choices/32axes/30personas/960reference values remain conditional
and unclassified. Formal classifier/threshold/tie/expertlabels still unavailable;
36animal semantics/reachability/accuracy BLOCKED. Word presence and raw scores
cannot establish bluff/polarize/range/exploit/balance validity.

This push updates existing PR124 only. No newPR, manualCI dispatch, merge,
controller/scheduler/heldstate or production operation. If automatic existingPR
CI runs, its exactHEAD result must be observed separately; localPASS alone is
notCI or browser/liveDBQA. No live DB/browser action was performed.

Next: observe existingPR CI; obtain authoritative classifier/versioned expert
labels for real36class boundary/reachability tests. Do not invent a classifier or
weaken the own-field schema to accept an unreviewed data export.

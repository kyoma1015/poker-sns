# C: native combo action values → exact 169-class transport

Status: PARTIAL product capability, locally verified; no equilibrium, generic
native infoset EV, historical G11, or full-poker convergence claim.

The new `gto/native/infoset_export.py` connects the existing common-infoset
`compare_hero_actions` native oracle to immutable combo records and a JSON-ready
169-class report. `PolicySnapshot` copies exact rational policies keyed by native
information strings. `from_solver` snapshots actual observed native average rows;
unknown/unvisited rows fail closed, and later training cannot change the snapshot.
The full copied policy rows have a canonical SHA-256 identity. This is not original
G11 ABI recovery or proof that the supplied policy is optimal.

`evaluate_combo` derives configuration/board/history/action identity from actual
inputs, retains native hero-information and opponent-support digests, and records
caller-supplied exact hero mass separately from observation-evidence and
hero-excluded counterfactual mass. The factory uses the real native legal replay
and action intervention oracle. Record objects are frozen data contracts, not
cryptographically signed attestations; arbitrary externally supplied records must
not be considered trusted execution receipts.

`export_action_classes` rejects duplicate/blocked hero cards or mixed
configurations, observations, policies and action order. It enumerates all
board-compatible concrete combinations for coverage. `observed_action_values`
means only the explicitly provided subset; `complete_class_action_values` stays
null until every eligible combination is represented and every positive-reach
record has computed action values. Even a complete class is conditioned on caller
explicit opponent beliefs, not proof of complete opponent support. The report
always preserves `native_infoset_ev: null`, `hand169_ev: null` and convergence
UNKNOWN. `report_json` transmits exact rationals as tagged numerator/denominator
strings, avoiding JavaScript integer precision loss. No frontend is connected or
production output published by this change.

## Evidence

`docs/qa/infoset-export-20261025/before.txt` is a missing-module baseline for a
new API contract, not a previously existing solver defect. New15 tests execute
against each real reconstructed Next/Cache/Packed module in separate processes.
They cover exact river action values, partial/complete board-compatible coverage,
identity refusal, zero/invalid mass, unknown policies, immutable input copies,
real native snapshot/checkpoint split-resume digest equality and exact JSON/null
transport. The complete-class coverage test uses deliberately copied record data
to test aggregation only; it is not full-hand poker strategy coverage.

Commands and all logs are in `runs.json` and adjacent text files. Native artifacts
used: `/workspace/work/gto-native-final-20261020/{g12_next,g12_p1_cache,g12_p1_packed}`.
Local total:375 unittest executions +25 packed-backend cases=400PASS/0FAIL.
This includes the unchanged3-case probability stub run once per variant (9)
instead of its normal once (3). Comparable existing workflow total is394 cases:
old349 +45 new. No test count is used as full feature completion evidence.

The exact serialized report agrees across all three variants:
`418f0a4bdca743b6d4e44fad0440654e01270e89aeb543b2a50e65d41d48d036`.
Existing native source payloads and old test files are unchanged. The existing
PR workflow gains only the new test invocation in its current bounded job; no
new schedule, manual CI dispatch, key, dependency installation, retained state
write or runtime activation is performed. The parent publisher must record the
new exact-head CI result; local PASS is not CI PASS.

## Remaining product gates

Caller belief completeness and hero reach provenance, supported native policy
coverage and validation, a reviewed UI contract/consumer, 169 native EV, full
2–9 players/20 owner stack settings/all sizes/rake/BB ante/MTT, representative
convergence and G9/G11 ABI/history remain incomplete. Do not fill missing EV.
Next: add an explicitly reviewed finite report consumer/UI only after agreeing
how exact rational values and coverage warnings are presented; independently
validate actual learned-policy coverage before any production interpretation.

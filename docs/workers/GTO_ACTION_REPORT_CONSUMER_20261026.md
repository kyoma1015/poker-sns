# C: read-only coverage-preserving action report consumer

Status: locally verified finite consumer capability; app integration, full poker
EV and original G9/G11 remain separate gates. No new runtime/model/DB operation.

## Usable offline flow

1. Produce `report_json(export_action_classes(records))` with the existing native
   combo oracle. The producer now adds `public_cards` and each combo's exact
   `action_values`; the existing v1 fields/null semantics remain unchanged.
2. Take observation/config/policy SHA-256 pins from an independently checked run
   record, not blindly from the same untrusted report.
3. Read the report through the bounded CLI:

   `python -B -m gto.native.action_report --expected-observation <SHA256> --expected-config <SHA256> --expected-policy <SHA256> --format html < report.json > report.html`

   Default `--format json` emits a reusable frontend-independent view. The static
   HTML requires no server, script, external asset or service. Its CSP refuses
   network/scripts/forms. The example is under
   `docs/qa/action-report-consumer-20261026/example-report.html`.

The CLI reads at most1MiB+1, rejects invalidUTF8/duplicateJSON keys/nonfinite or
float numbers/depth>24/oversized JSON integers or rational digits/unknown fields,
and emits only `INVALID_ACTION_REPORT` on rejection. Rational JSON numerator and
denominator strings are parsed as exact Fraction; no float/JavaScript safeinteger
rounding is used. Output rational display uses exact integer or n/d strings.
No input text, file path, secret or traceback is included in CLI rejection.

## What validation proves

- Caller pins match exact observation/config/policy identity strings.
- All169 class names and action order are known, cards distinct/unblocked, concrete
  combos not duplicated, counts and mass consistent.
- New reports independently recompute board-compatible eligible counts, perclass
  observed counts, reachmass and weighted action means from individual combo data.
- Missing/partial values stay null; fullclass values cannot be promoted without
  all eligible combos and positive-mass computed values.
- Generic native_infoset_ev/hand169_ev remain null, convergence UNKNOWN. Support
  completeness must remain false. Neither visits nor actionEV is turned into
  action frequency. The UI explicitly displays frequencies as unavailable.
- Old v1 reports lacking board/percombo values are accepted only as legacy
  structure, with LEGACY_PROVENANCE_NOT_RECOMPUTABLE and all values withheld.

The hashes are callerpins, not a signature. Arithmetic consistency cannot prove
input execution authenticity, complete beliefs, correct strategy, original ABI,
optimality or convergence. The view never claims those. The existing native
frequency bridge is intentionally NOT combined: its caller reach and board/history
context must independently match; frequencies cannot be inferred from actionEV.

## Executed evidence

Before: new module missing (ModuleNotFoundError). This is a new API contract
baseline, not a claim of an old solver defect. New15 cases use actual native
producer → consumer and real stdin subprocess CLI. They cover legacy withholding,
exact rationals, identity mismatches, tampered means/masses/counts, injection,
malformed inputs, HTML escaping, null EV and unavailable frequencies.

Runs: `docs/qa/action-report-consumer-20261026/runs.json` and adjacent logs.
Next/Cache/Packed separate processes using existing fully reconstructed modules:
`/workspace/work/gto-native-final-20261020/{variant}`.
420 unittest executions +25packed cases=445PASS/0FAIL. Includes6extra existing
stub repetitions; normal existing CI comparable target is439=prior394+45new.
No prior acceptance or test file was modified. Existing workflow adds one new
consumer test command in its already bounded job; parent handles publication/CI.
No npmci/build/lint: no frontend/Node source or dependency changed.

Actual producer/consumer view SHA is identical across all3 variants:
`9ce7e47be33e71f2df2d7e59346fbe66e3ea01155c5b3766993c7fa9cfe4ed38`.
HTML SHA:
`5f7c637eb84109327a84ae74499d72358f127b5d15a7d3ae758c541a1d663cc2`.
Payload hash verification succeeded. No native reconstruction/recompilation was
needed; no original source/checkpoint was overwritten or loaded.

## G9/G11 evidence inventory

Present preserved files: `handoff/gto/compressed/g11_rules_embed.h.zlib.b64`,
`handoff/gto/g12_next/g11_native_state.h`, transferred3solver/rules/backend data,
`handoff/gto/check_vendor_bundle.py`, source-discovery document
`docs/handoff/GTO_G11_PACKED_SOURCE_DISCOVERY_20261020.md`, reconstruction manifest
and new-run checkpoint regression. Hash-check output is saved beside consumer QA.

Still unavailable/unproved in this branch: original G9 nine-player baseline source
and acceptance, received original1,588vendor closure, original interpreter/compiler
ABI manifest and matching build binary, historical complete checkpoint+RNG/meta,
owner20stack/allsize fixture list and original expected baseline results. Relevant
existing references: `gto/README.md:63` and
`GTO_NATIVE_TRAINING_BATCH_20261023.md:67–68`. Presence of a header/hashledger is
not receipt of original vendor or checkpoint. All historical compatibility gates
remain BLOCKED/UNKNOWN; no historical checkpoint opened.

Next: reviewed app presentation consumer with exact provenance/coverage warnings,
actual native frequency contract matching (board/history/config/policy/reach),
validated broader learnedpolicy support and original baseline acquisition. Do not
remove final2–9players/20stacks/rake/BBA/MTT/allsize/169frequencyEV specifications.

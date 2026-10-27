# Verified-only preflop range search integration

Input public74bddc3338e0d532d9cff4286b7204116fc0915e (localf69ec0c, same
tree32f60ee957f486c26c1acd6a6f96e8792995f2be). CI40452812571 SUCCESS,
decoded job122019228959:585unittest+25Packed=610PASS (previous526,+84).
Three-variant400iteration learned snapshot+three-way action report bytes agree:
SHA2563e4d696fc68d8f4add121de7223d4453c59ae2dd235e323932c8501827dafa25.
This is reproduction evidence, not convergence certification.

UI acceptance: exact input matching;169cells; no invented unknown frequency/EV;
no sampled/drift/local-only artifact accepted as verified GTO; no stale result
after query changes; full-game reviewed certificate plus complete169/1326 data
required before display; existing SNS/TDA/diagnosis and auth behavior preserved.

Implementation:
- `/gto/preflop` route and one tool-card entry. These3shared-file lines are the
  only App.tsx/PokerTools.tsx changes, needed for the requested GTO navigation.
- MTT/ring,2..9seats/native seat-position mapping, stack, BB ante, rake/cap,
  open/3bet/4bet sizes and target stage. Values match exactly; no interpolation.
  Blank stack/size inputs have illustrative placeholders, not invented formal
 20stack/sizing presets. Full formal configuration acceptance remains blocked
  only where the original fixture set is required.
-169matrix, selectable hand frequencies/EV, coverage, calculation/policy identity
  and whole-target-game unilateral-deviation bound metadata for accepted data.
- Trusted build-time certificate registry, currently EMPTY. Parser rejects
  partial coverage, null/nonfinite EV, malformed frequencies, mismatched query/
  policy/config, missing review entry, sampled-only/local-drift certificate or
  showdown shortcut. The parser is a transport/release boundary, not a Nash proof.
- Existing sampled/native learning schemas intentionally cannot pass this gate.
  No production-facing arbitrary JSON upload or user-controlled certificate path.
  Engine-to-UI verified-result acceptance contract is present; actual accepted
  verifiedGTO datasets0. The app honestly displays unavailable results, not a
  fabricated playable range. Real full-target-game certificates are still needed.

Validation:
- Local Node24:8GTO data-contract tests PASS with `--test-isolation=none`.
  Default process-isolated runner in this executor reported only a file-level
  result; we did not count that as8executed assertions. TAP log retained.
- Separate GTO UI CI installs exact lockfile dependencies, runs8Node tests,
  app build/typecheck/lint and6isolated Chromium checks. Pending exact-head CI.
- Browser positive fixtures are explicitly synthetic, imported only by the
  isolated test entry under tests/, not src/gto/verifiedCatalog.ts or app entry.
  They verify rendering only and do not increase real169EV/GTO coverage.
- Browser test blocks external requests, uses no Supabase/auth/real accounts.
  Production-empty catalog,2..9position mapping, unsupported condition states,
  fixture frequencies/EV and stale-result clearing are checked.
- Native CI also runs on GTO UI source changes, so current head has fresh native
  and app evidence. Expected610native/backend+8Node+6browser=624executions,
  pending actual decoded CI evidence; build/lint are separate checks.

React review checklist: hooks unconditional; derived positions not effect state;
all controls labelled; keyboard-focus styles and scrollable labelled matrix;
button types explicit; live result status; no network waterfall or extra library;
typed query/results and data guards; query edits clear old data immediately.

Remaining release requirements: complete learned joint support, formal profiles,
actual representative strategy convergence and verified169frequency/EV datasets.
UI implementation is not evidence that any real GTO release condition is solved.
Next: full opponent reach/169aggregation and convergence evidence, then populate
only independently reviewed full-game data. No production/main/billing actions,
no independent restart or scheduler enabled.

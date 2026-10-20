# Issue22 B audit CLI boundary fix — acceptance before changes
Base PR14 4e16f7a7b567237d2735f1392906a6b1de2b7c23.
Scope: offline CLI boundary and its unit tests only; no question publication, UI, scoring or DB changes.
Observed defect: the CLI catches JSON.parse errors and prints error.message, which may contain a raw input fragment. This violates its own no-payload-in-logs comment and can leak private draft question text.
Also inspect invalid argument boundaries: the current two-variable destructuring silently ignores trailing arguments and interprets oversized expected counts later as data failures.
Acceptance: raw malformed JSON and read-error details never reach output; stable reason codes, exact argument count, positive safe count validation, correct exit status; valid audit output remains compatible and never authorizes publication. Actual published350 and official-rule correctness remain UNKNOWN.

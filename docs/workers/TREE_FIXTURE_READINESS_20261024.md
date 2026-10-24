# Process-fixture readiness root causes and bounded synchronization

Start ac7714aa7b5d18d80dc44dfdd763d4381e26f99b matched GitHub. Two independently reproduced fixture races explain the observed timing failures; neither is evidence of a production-worker correction.

1. `owned_tree_probe` started its0.4s worker.command timeout before the parent/child/grandchild topology completed Python startup. A fixed0.65s parent setup delay reproduced missing ids.json (1FAIL at9f3961a). Fixture-only Popen readiness waits at most2s before returning the actual process to the unchanged worker.command, so the original0.4s runtime timeout and real cleanup begin only after full topology readiness. ids are atomically published. Same fixed1PASS; inherited topology expectations still require SIGKILL/reap and explicitly UNKNOWN detached liveness. Setup failure has its own bounded failure, not cleanup success.

2. The generated stdin-death fixture worker published source.py by write_text, whose exists became true after truncate but before contents. Fixed delayed-write/snapshot scheduling reproduced retained empty bytes followed by populated bytes (1FAIL at943549a). Only generated-worker publication changed to source.pending.write_text then atomic replace(source.py). Original timeout, assertions and expected content remain unchanged. Fixed1PASS; instrumentation verifies one injected slow write and two snapshots actually occurred.

Final automation142PASS plus worker_acceptance85PASS=227PASS. These include the previous225 core and two new fixed tests. Existing queue/defer/resume, trusted pin lifecycle, finite limits, UNKNOWN refusal and actual temporary commit-boundary cases are reused without adding another preflight/controller abstraction. No formal auto-restart connection was made. Full logs preserve earlier first-run timing failures instead of replacing them with retry-only success.

Integrity: `integrity.json` records baseline/final SHA256 of all starting tests. Two existing fixture files intentionally differ: owned_tree_probe.py and test_worker_tree_boundaries.py; all other baseline tests remain byte-identical. The latter changes only generated worker atomic publication; it does not weaken an assertion. Retrieve exact originals using `git show ac7714aa7b5d18d80dc44dfdd763d4381e26f99b:<path>`. Do not claim all original37 files are unchanged in this cycle.

Evidence: docs/qa/tree-readiness-20261024/. No protected expectation removed, no production script change, no retained SQLite access/modification, new PR, manual CI, schedule change, formal host connection or controller adoption. Independent startup remains UNKNOWN; unattended OFF; poll NO-GO.

Next: review setup-readiness contract separately from runtime cleanup deadlines; continue external trusted-store auth/deadline design under existing approval. Any actual host/controller connection remains separately gated. Restart from this branch HEAD and retain fixed baseline commits and failure logs.

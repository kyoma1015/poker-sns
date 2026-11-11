# C selective main-based integration — 2026-10-22

Base main: 7da31f078624178dbddf8f1edf59eb8d0bf782b7.
Source: PR66 b492f8c7730cb5ebb66beee909ba2526dcb7cc85.
Only minimum GTO regression closure is transplanted; no branch merge, poll/SQL/UI
or unrelated handoff/backends are copied. Main remains unchanged until review.
Exact source/destination byte hashes and each file's purpose are in
docs/qa/gto-main-integration-20261022/TRANSPLANT_MANIFEST.json.

Before transplant, `python -B -c 'from gto.native import settlement'` failed with
ModuleNotFoundError: main had no gto module. The unchanged original40 GTO tests
and fixed29 C acceptance run in isolation. The five fixed files retain exact
bytes but move to gto/integration_acceptance so they cannot absorb another lane's
worker tests. Their imports have no location-dependent ROOT assumptions.

Commands:
```
python -B handoff/gto/verify_native_solvers.py
python -B -m unittest discover -s gto/tests -v
python -B -m unittest discover -s gto/integration_acceptance -v
python -B gto/native/verify_integration.py --wheel /path/to/pinned/pybind11-2.13.6.whl
```

The launcher strictly Base64/zlib decodes, bounds and verifies original Rules.py
10318 bytes / SHA456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a
and Ledger header10159 bytes /
SHA870b64c0253be86ef139d0c2437d202d9d4f10097e871dd8bde526402dd49353.
Only SHA237c41e29157b962835d356b370ededd57594a26d5894a795960f0047cb5caf5
pybind11 wheel headers are extracted after hash verification. No pip install or
Abseil is needed for this test-only bridge; all outputs use an owned temporary
directory outside source. The original three solver payloads are verified as
bytes only; they are not rebuilt here.

This candidate proves neither original G11 vendor/ABI compatibility nor actual
poker strategy convergence. No historical checkpoint is resumed or modified.
The previously recorded positive_live/dead-ante rule edge remains unresolved;
no house-rule policy is selected. No DB, production, billing or Vercel operation.

Local verification (2026-10-22): PASS3 original solver payload hashes, PASS40
existing regressions, PASS29 unchanged fixed C acceptance, PASS5 launcher boundary
tests, and PASS17 settlement + PASS16 rank7 native bridge comparisons. Commands
and measured output are retained under docs/qa/gto-main-integration-20261022/.
The native bridge was rerun after switching wheel extraction to the same hashed
in-memory bytes. CI is defined here but has not yet run for this unpublished commit.
Latest externally reported main d8b3687f058227ce8a779d463262d4e2b6fad536
changes only the poll release runbook; this candidate preserves its fixed base.

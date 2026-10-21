# Settlement expectation preflight — fixed input, before implementation

Evidence: Issue22 and `gto/README.md` / prior acceptance require both kernels to
match explicit hand-derived expected chip results, not only each other or chip
conservation. At PR57 source c73b57d156e3c1aae24e10565787df4d73b1c3a8,
replacing all 17 owned synthetic cases' `expected` mappings with `{}` still
returns `PASS`, case_count17. This is a vacuous oracle check; it is not a defect
claim about the preserved poker kernels or a new house rule specification.

Review scope: only `gto/native/settlement.py`. Before opening the reference/native
kernel, every case must have a nonempty JSON object `expected`; otherwise raise
ValueError. Do not alter valid expectation fields/values, source fixture bytes,
reference archives, solver code or historical checkpoints. Preserve the valid17
cases, rank7 and checkpoint-budget regressions. The fixed test includes a wrong
nonempty expected net to ensure actual equality comparison still fails.

Commands: `python -B -m unittest discover -s tests/worker_acceptance -v` and
`python -B -m unittest discover -s gto/tests -v`. Tests use only private temporary
JSON copies of synthetic fixtures. No dependency installation/native build/DB.
This is validator hardening, not strategic accuracy, convergence or G11 parity.

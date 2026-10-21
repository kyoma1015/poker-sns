# Pinned PR overlap review

A shared filename is a reason to review, not proof of duplicate implementation.
`Continuation.plan` still requires fresh complete provider PR file/head snapshots,
immutable task/input/failed acceptance, dependencies, no live lane lease and no
existing task/branch. No PR number is globally ignored.

A pinned inherited head that Git proves is an ancestor remains supported. For
other reviewed cases, `candidate.overlap_reviews["PR_NUMBER"]` must include
`reviewed=true`, a bounded concrete `reason`, `candidate_base_sha`, `head_sha`,
`pr_base_sha` matching the fresh observation's `base_sha`, and exact `files`
coverage of every shared allowed path. Each file pins `candidate_blob` and
`head_blob` to the actual complete Git blobs and chooses one proof:

- `equivalent_blob`: whole source file identical, even across cherry-picks.
- `ancestor_blob`: `witness_commit` must be a Git-verified ancestor of the
  candidate input whose whole file blob equals the observed PR head's file.
  The prior implementation is present historically; later corrections need not
  be discarded to make the current file match an older PR.
- `included_patch`: `patch_sha256` pins exact per-file `git diff --full-index
  --no-ext-diff --no-textconv --no-renames --binary --src-prefix=a/
  --dst-prefix=b/ PR_BASE PR_HEAD -- PATH` bytes. That nonempty patch must
  reverse-check cleanly against a private index of candidate input. Temporary
  index/object storage prevents writes to the actual source, index or refs.

All commit/blob pins are full SHA values. Source paths must be regular bounded
files; arbitrary patterns, missing objects, unknown modes, changed pins, partial
coverage and unproved pending changes fail closed. Empty patch certificates are
refused. The host must still review the distinct task purpose and independently
witness the failing protected acceptance. A certificate proves inheritance of
bytes/patches, not all semantic behavior, CI, production QA, release permission,
or whether merging both PRs is appropriate. Keep original branches and review
which successor is the canonical release path.

Changed proof metadata under a previously stored immutable candidate ID is
rejected. Use a newly reviewed versioned candidate/task ID instead of rewriting
history. The controller's exact allowed source, protected tests, source-after-test
and staged hash, lease, replay, no-op and zero-test checks are unchanged.

Fixed fixture acceptance covers equivalent independent history, exact included
patch with later unrelated corrections, historical ancestor proof, advanced pins,
wrong blobs/digests, missing/extra paths, unknown/no-op proof, unproved pending
change, source/index preservation, and actual planner selection with failed
baseline still required. Fixtures are not real host implementation evidence.
No new runtime, credentials, paid service, production DB or merge is installed.

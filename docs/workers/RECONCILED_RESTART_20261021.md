# Reconciled implementation restart — 2026-10-21

The old blanket same-filename blocker is replaced by PR38 scripts/pr_overlap.py + Continuation.plan. Never use the old PR34-only planner for new dispatch without this reviewed extension. No PR ignore list, weakened acceptance or force-merge was added. Full29PR original audit,41 ancestryedges/165 sharedfilepairs and exact blob proofs are under docs/qa/pr-overlap-20261021/.

## Completed implementations
A PR37 ef6a26299f6e35a33bc3a5cf61ce7b78a68081a6: offline poll catalog review, fixed10PASS; always REVIEW_REQUIRED at best, no DB or release approval. CI39585992898SUCCESS.
Infrastructure PR38 source2fcd124d06e2627a1436f2123a7fdc9ce41df95f: exact equivalent/ancestor/included-patch proof, fixed24+worker22+queue15PASS; CI39586004703SUCCESS at7bba86fb3d1206a76361b7e0a3eda4b01948b684.
B PR41 sourcef6ba3739ca4a61a9fd47accbcb2af7be3993694a, headc08654d487ea4f5a6dcda79a26e25ff693a1ba84: search latest-response gate and transport recovery. Fixed5PASS/oldquiz6PASS/build/lint; original14 savedanswer tests restored without alteration; CI39586338980SUCCESS.
C PR39 66033db8806838722a4cf7c4965542ac86903776: exact positive int checkpoint budget, fixed11/old40PASS; CI39586016041SUCCESS.
D PR40 4dab60e1782ad8923320977488d6962efef7fc4b: fixed save/share errorcopy, acceptance4/unit100/mobile6/build/lintPASS; CI39586228371SUCCESS.
All were actual formal host dispatches after sharedlease preparation; root rechecked fixed tests/sourcehashes/commit. Public resultJSON under host-results/. Private tokens, receipts and SQLite NOT copied. Main, productionDB/deploy/billing untouched.

## Legacy PR resolution
C21 source exactly matches input. B21/11 and D21/10 source exactly matches verified ancestor versions; later corrections preserved. Their paths are not new duplicate work. PRhead/base and all sourceblob pins are mandatory; changed head or unmatched bytes blocks.
B19 could not pass exact-source/patch proof. A NEW input branch performed normal merge of all17 PR19files, resolved6 conflicts individually with current canonical source/config bytes preserved and unique historical QA/workflow retained. No ours strategy or originalbranch overwrite. Fixed5FAIL baseline and protected3hashes unchanged. New base7ee09c1b3bf71a75e3889951d7520bf3347ba375 has PR19 as real ancestor. Integration evidence is in that input docs/qa/pr-overlap-20261021/B-PR19-reviewed-integration.json.
Keep old PRs/branches as history; do not merge both legacy and successors. F03 notification release remains separate from poll-only PR31; PR13/21 are historic integration checks, not wholesale release candidates. PR27count fix is already in31; PR28/29/30 independent audit/mass/persona fixes still need selected reuse, do not lose or blindly double-merge.

## Already prepared next inputs
Reviewed exact candidate/manifest/ready-plan JSON under docs/workers/ready-next/. Root verified sourceGitobjects/protectedhashes and fresh complete34PR snapshot; B,C,D each returnedREADY1 with no blocked reasons using actualsharedstate. Readiness is time-specific, rerun fresh PR/CI/lease checks. No next-source worker has started yet.
B next: issue22-b-search-data-v1, input16b02a76165a07f3ec1c8a1389705cdb13b27739 (codex/issue22-b-search-data-input-20261021). Fixed9: old5PASS/new4FAIL malformed raw RPC rows; prior14 answer tests retained.
C next: issue22-c-nonempty-settlement-v1, inputa1ec880c66b54fba67fc16bee0d51f56482e9e81 (codex/c-settlement-nonempty-input-20261021). Fixed14 currently4FAIL/2ERROR for empty/non-list cases falselyPASS0; valid17 synthetic settlement retained. Pythonstdlib sourceonlygto/native/settlement.py.
D next: image error redaction input3aa1a2ee02f442fd3983217e19d37607d7cb6a78 (codex/issue22-d-image-error-input-20261021). Fixed6:5PASS/1FAIL PNG error marker; PNG retry/dimensions/filename/stale gates protected.
A next realcatalog/privacy/Auth proof needs an authorized nonproduction environment; offline classifier is not production parity approval. Do not connect production to manufacture a task.

## Next ordinary reservation implementation proof
Use the EXISTING finite recurring reservation, unchanged6h/COUNT28. Prior one-off probe is consumed and not recreated. Root updated only the ordinary prompt to consult this new version/ready catalog, prioritize C next for max1 scheduled proof, use same existing state and fresh gates. Do NOT dispatch C source manually before the scheduled instruction arrives if recording scheduler-to-code evidence. Scheduled prompt arrival must be witnessed, then provider metadata inspected without inventing runID; old original4spec_hash continuity verified; plan→prepare→actual formal collaboration→trusted root receipt→finish→publishDraftPR→CI. A callback in an already-active host is not an independentcoldstart daemon.
Shared private state: /workspace/work/issue22-host-controller/leases.sqlite. Existing root controller checkout: /workspace/work/issue22-reconciled-worktrees/issue22-overlap-proof-v1. Missing state/capabilities→read-only. No CLI EROFS retries, authcopy/HOME relocation/sandbox bypass/newAPIsecrets. Dependencies outside preparedsource, cache private temp. No activelease stealing, preserve failedworktrees, max1 retry.

## Remaining release/accuracy gates
Poll31 isolatedDB56PASS remains synthetic schema/JWT, GoTrue absent: actualcatalog/policyACL/cronsemantics/realDBUI/CLIhistory-advisors/ownerSQLbackupfullACLrollback/deployrights pending; Vercel403 untouched. TDA350 official correctness, diagnosis36 semantic validity, originalG11/checkpointcompat/convergence remain unverified. Synthetic native parity is not a strategy proof.

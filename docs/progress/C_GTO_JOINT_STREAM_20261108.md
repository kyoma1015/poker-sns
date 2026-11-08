# GTO PR120 / full-population streaming

Initial remote/local c1855e86128eeaf5a7446c699dce91d4dd4836ea, clean, no later
work on remote. Prior6SUCCESS runs not manually rerun. Formal0/12 retained.

Implemented joint_stream.py/.cc: one-board RAM, shared preflop snapshot across
all1755orbits, weighted gradient accumulator, one global preflop update per
complete epoch. Counterfactual reach excludes own reach. Continuation rows retain
own169+flags/publicflop/history. Independent BR exports terminal own-class CF
values; integrate all board chance before preflop maximization. Exact reference
parity and atomic rollback/resume tests7PASS locally. Pinned old sources/UI/data
are unchanged. Initial source/protocol commit e41d6abeeb717b9c712ed1dda180c612a8168930
was created before the first full epoch finished; this is local preregistration.

joint_stream_cache generates all1755fine-private/card-removed exact990-runout
moments. Producer identity/checksum enforced; prior3blocks reused only after
fresh independent equality. Cacheworkers even/odd are finite processes with
3600second budgets; no daemon or restart installation. Current study evaluates
frozen-small then completed joint epochs1,2,4 where budget permits. Report every
completed epoch, including worsening; no model selection from final evaluation.

This record is PRE-RESULT: population BR/NashConv UNKNOWN until evaluation ends.
Do not promote previous28/22100 values. Current experiment all1755 is research
only with one flop raise/three sizes/checkthrough later streets, not fullNLHE.
Original20stack/fullsize authority absent, no matched externalGTO acquired.

Workspace:
- /workspace/joint-stream-cache: versioned reusable moments
- /workspace/joint-stream-run/learned.sqlite: atomic shared/postflop CFR checkpoint
- /workspace/joint-stream-full.sqlite: preserved64block pilot snapshot
- /workspace/joint-stream-run/frozen.sqlite: readonly frozen-baseline evaluation
- /workspace/joint-stream-{even,odd,train1,study}.log and output JSONs
- /workspace/joint-stream-supervisor.py: finite supervised continuation, no restart

Resume safely:
1. Check latestremote,localHEAD,status and running processes. Never launch a
   second writer/evaluator for the same checkpoint. study operator.lock guards
   its phase family; low-level CLI assumes one operator. Do not train/evaluate
   overlapping phases or bypass the lock. Incomplete epochs cannot be evaluated.
2. Complete missing cache blocks with joint_stream_cache --parity0/1 (source
   identities must match). Never0-fill missing cache; budget stops preserve state.
3. Resume joint_stream_study --root /workspace/joint-stream-run --cache
   /workspace/joint-stream-cache --seconds3600 after the current train1 process
   finishes. It skips saved completed checkpoint results and resumes exact cursors.
4. Record full-population baseline/epoch BR, numeric bounds,169row exports and
   resource measurements in QA results; then push normal FF and verify new CI.
   CI short job verifies monolithic equivalence/restart/population and artifact
   guards, NOT a full1755numerical replay; local population measurements must
   remain distinguished from CI test coverage.
5. Qualify continuation approximation/additional actions; recover formal sources
   and matched references; only evidence-qualified policies may enter normal UI.

No main/prodDB/Storage/Vercel/SSO/billing/otherPR change. No force/reset/clean.
Draft maintained. Existing ranges/HU1BB/2–9 regressions/static demo retained.

## Live continuation after initial source publication

Remote/local source fix21e4fea57462fde226b951b5ac6d64748feadf4d, local additional
warm protocol commit3e7548b retained; no destructive synchronization. All1755cache
blocks generated,22100physicalflops. First budget3600s stopped at epoch2/cursor1673;
next invocation resumed it, finished epoch4 and is evaluating that checkpoint.
Completed full-population frozen baselineNC0.932107152722,epoch1NC7.945002097774,
epoch2NC5.582643557700BB. Worse than frozen, not qualified. All actionEV4563cells
against the saved independent fullclasspair oracle match to1.78e-13BB; complete
28561classpair chance differs from theoretical blockers by<=2.20e-18; allinEV
diff<=3.12e-12BB. These are numerical consistency, not externalGTO proofs.

Additional bounded positive-regret warm trial is registered in WARMSTART.md;
checkpoint /workspace/joint-stream-warm/learned.sqlite, log /workspace/joint-stream-warm.log,
runner docs/qa/joint-stream-20261108/run_warm.py (PYTHONPATH repo root). Target2epochs,
3600s, no sameDB concurrent operators. It is a post-observation optimization,
not a new blind holdout. Report its failure/worsening as well as uniform results.

Pending new research-row adapter gto/abstract/joint_stream_export.py exports
RFI/vsopen/vs3bet/vs4bet169rows with raise sizes converted from chips toBB and
explicitly rejects ordinary admission, partial coverage and missingEV. Tests wait
for completed epoch4 artifact; do not count skipped tests asPASS. Existing UI is
still unchanged. Full population/source/frozen manifests and actual resource
fingerprints are in /workspace/joint-stream-*.json. Capture final results/CI into
QA and PR before declaring this batch finished.

## Completed uniform population checkpoint

Epoch4 full independent BR complete:NC3.081906371316BB,SB/BB root gains
1.772423264578/1.309483106738BB,SBnetEV-0.057020265468BB. Board chance coverage
1755/1755=22100/22100;model/action uncertainty remains,0.1BB criterionFAIL.
Frozen full-profileNC0.932107152722BB is still better. Results and all1755moment
fingerprints now in QA. New research-row adapter and all12local testsPASS, no
skips. RFI/vsopen/vs3bet/vs4bet169each exported with proper BBlabels/positions;
ordinary admission hard-rejected. No new data is imported into existing UI.
Warmtrial is stillRUNNING; no warm quality result claimed at this snapshot.

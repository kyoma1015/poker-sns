# Pre-registered generalization development
Base public2b2f88f945d0a09abb7e5bde0d70d7c60f0b80a4, clean shadow4ed5374.
Protocol saved BEFORE candidate implementation/evaluation. Train18,validation6,
final6, six board-structure strata; suit-isomorphic overlaps and all previous6
boards excluded. Seeds,teacher budget,candidates,selection and final acceptance
in docs/qa/generalization-20261101/protocol.json. No final-test policy selection.
Commit protocol first locally; commit selected policy lock BEFORE final phase.
Publish ordered evidence commits in ONE branch-ref update to avoid duplicateCI.
Own-uniform-equity feature integrates ALL unknown compatible opponents equally,
not the actually dealt opponent. Exact same rich-signal/4arm game evaluates
baseline and candidates. Expanded information can increase BR strength; do not
compare directly with previous coarse-signal NashConv as identical conditions.
No existing CFR integration/normalGTO publication/main/prod/otherPR/fees changes.

## Selection lock BEFORE final evaluation
New9tests PASS. Implementation was committed before validation execution.
Only train18/validation6 used. Seven candidates,24validation contexts each.
Predeclared winner:knn9_private8_board0.5. Validation mean restrictedNashConv
1.203344937BB vs retrainedcoarse2.420913209BB; worst4.532968948 vs4.187177033BB.
Selection minimizes mean per initial protocol,NOT a posthoc worst-case override.
This worst-case risk is preserved,not hidden. Final6boards not yet evaluated.
selection-lock.json binds selection/protocol/source SHA. Commit this lock before
calling --phase final. Final phase has no fit/solve/choose-candidate calls.

## Locked final and post-lock read-only audit
Final selected meanNC.847890988BB vs retrainedcoarse1.852747222 (54.2360%
reduction);worst1.285742859 vs3.586962355.2/3preregistered criteria PASS,
absolute max<=.1BB FAIL. No reselection/tuning after final. Old-frozen policy
common-game finalmean3.599278277,worst9.342048524; richer signal/different
boards mean these are not directly the previous coarse-game NC numbers.
Same selected student's train mean.009425077,worst.028919048;validation
mean1.203344937,worst4.532968948. Generalization gap remains; not merely
insufficient teacher iterations. Teacher maxtrainNC.028892827.
Independent rich-game priors/model selection/final no-fit verified10testsPASS.
Post-lock auditor evaluates train/validation only,never fits/chooses/reads final.
Old helper dependency manifest and selection-byte lock checked inCI.
CI repeats train/validation selection,uses the committed locked selection for
final,same sources,then readonly training audit,all with1e-12/hash comparisons.
Final equal-balanced structure distribution is research-only,not real chance.
Formal0/12. No originalCFR connection/normalGTO/UI/prod/main/fees/otherPR changes.
## Resume
Check latestpublicHEAD/dirty files/rawCI. Read QA README/protocol/selection-lock.
Next study must exclude the30current board suit-orbits and allprevious6 from
its NEW final set before feature changes. Investigate range-aware own strength,
transfer function and uncertainty using TRAIN/VALIDATION,not final retuning.
Broaden real-game response/reference only after restricted validation passes.
No externalGTO comparison performed. AUTO-RESUME/independent restartnone.

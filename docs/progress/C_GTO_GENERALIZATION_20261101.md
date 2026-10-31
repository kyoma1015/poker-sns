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

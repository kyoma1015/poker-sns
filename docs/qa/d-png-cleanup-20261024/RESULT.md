# PNG download exception cleanup
Startdf91a23ccca19a2047aed50ec22808dc5613f678, existingPR124.
Actual downloadShareImage function is extracted from component source, with only its Blob/HTMLAnchorElement type annotations stripped, then executed by node:vm with isolated DOM/URL/timer stubs. This is real-function fault injection, not React or browser E2E, and no image rendering/DB/network operation is performed.
Fixed5 tests before1PASS/4FAIL ->5PASS/0FAIL. createElement,appendChild,click,remove exceptions previously bypassed objectURL revocation scheduling; finally now always attempts link cleanup and schedules30second URL revocation. Successful filename/click/timing unchanged. A download error is preserved if remove also fails (code); the single-fault cases are measured. Timer failure/process termination is outside the measured guarantee.
Prior110regressionsPASS; total115PASS/0FAIL. Existing source43e2bae,1d8fdfe,4aed33e and1c7ccad has same unguarded cleanup. Navigation/PNG rendering/doubleclick changes are not reimplemented; only cleanup boundary changes.
Scores/questions/classifier/DB unchanged. Formalclassifier/thresholds/ties/expertlabels remainBLOCKED, not inferred from tests.
No mainmerge/newPR/manualCI/production/heldstate/host/scheduler operations. Existing branch normal push and automatic PR124 CI only.

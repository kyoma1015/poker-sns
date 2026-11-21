# Separate measurement-only completion; original budget was NOT sufficient

Original3method workers+amended third epoch used the7200s per-method cap. All
three epoch3 TRAINING states are complete/cursor0, but final evaluation coverage
is vanilla-linear72.760181%,CFR+64.542986%,DCFR68.524887%. Original checkpoint3
comparison therefore remains PARTIAL at that cap, not claimed completed on time.
Full2epoch results are known/worse than baseline; full3epoch outcomes are unknown.

A separate READONLY-POLICY measurement phase is registered now, before reading
any complete3epoch BR:1800seconds operator/per worker, same2CPU/8GiB cgroup,
same caches/game/checkpoints, all3candidates mandatory, remaining boards only.
No extra training, no changes to regret/average arrays, no new candidate selection,
no threshold relaxation, no subsequent extension. Preserve original partialJSONs
under cap7200/ with hashes. Resume ONLY eval:sum; record checkpoint-state hashes
excluding eval:* before/after to prove no learned policy changed. Results must
report this1800s ADDITIONAL evaluation allocation separately from original7200s.
If incomplete again, report remaining safe intervals/UNKNOWN without more time.

The extra measurement is required to compare regret schedules (which first differ
in epoch3); it does not adopt any worse-than-baseline strategy or constitute a
blind validation. Formal0/12,normal0,externalNOTPERFORMED remain unchanged.

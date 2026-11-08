# Counterfactual-update audit and registered population comparison

**Research engineering CONDITIONAL PASS;0.1BB quality FAIL;release BLOCKED.**
Full1755orbits/22100flops/9continuation branches,shared preflop info unchanged.
Original sources/frozenCFR/UI/demo/ranges are protected; no ordinary admission.

|Method|epoch1 NC|epoch2 NC|epoch3 NC|epoch3 SB/BB BR gains (BB)|
|---|---:|---:|---:|---|
|Frozen baseline|0.932107|not updated|not updated|0.490803 /0.441304|
|Historical vanilla uniform-average|0.932107|1.190820|not rerun|epoch2:0.610933 /0.579886|
|Vanilla linear average|0.932107|1.475249|2.473734|1.349612 /1.124122|
|Simultaneous CFR+linear|0.932107|1.475249|4.888657|3.388390 /1.500266|
|DCFR(1.5,0,2)|0.932107|1.775081|3.726963|2.232042 /1.494922|

All completed registered outcomes retained; no newly trained strategy adopted.
No4e-16 roundoff claimed as improvement. Selfplay SB EV increases are not improved
equilibrium quality. Full3checkpoint results/raw actionEV and frequencies are in
checkpoints/*.json.gz,standard gzip/JSON; research-only3x4x169ranges in *ranges.gz.
3candidates x676rows=2028research rows,6084actionEV cells. NewUI data0,normal0.
Small analytic-game witnesses are explicitly NOT HU50 EV measurements.

## Findings
AUDIT_FINDINGS.md and audit-results.json: independent explicit path and64pureBR
oracles match nativeCF/own-average weights,signs,sharedfuture-hidden preflop.
A behavioral epsilon prior is not inherited regret history; near-equilibrium
analytic witness and convex-NC lower bound isolate legitimate early overshoot.
No core discrepancy found in bounded tests; no claim all code/full NLHE is proven.
Training-only kernel retains bit-identical gradients/averages,three sampled CPU
reductions27–31%. The evaluator still uses the unchanged fullBR kernel.

## Preregistration and actual budget disclosure
PROTOCOL.md/registration.json were stored before training. Structural AMENDMENT
adds epoch3 before any epoch1 BR outcome was available; original2epoch record is
retained. Original7200s/method and10800s operator,2CPU/8GiB cgroup,newdata8GiB.
2epoch workers finished in5140.214582s; at7200s cap epoch3 training complete but
BR coverage72.760181/64.542986/68.524887%,with safe intervals retained cap7200/.
MEASUREMENT_COMPLETION.md is a separate,disclosed1800s measurement-only budget,
no additional training or selection. It finished421.565219s wall; maxchildRSS
626452KiB. All3non-eval policy-state hashes identical before/after extraBR.
Original budget was insufficient; do not report all evaluation inside7200s.

## Validation / scope
Local26stream/update/report testsPASS; old protected dependency manifestsPASS.
Current final-head CI must be confirmed separately. ShortCI tests correctness,
identities,gzip hashes and report guards; it does not replay every population
kernel. Chance/runouts are exactly integrated in this limited abstraction;
statistical samplingerror0, numericalguard1e-8BB. Omitted sizes/secondraises/later
betting/concrete-private abstraction remainUNKNOWN for actual poker accuracy.
No trusted same-condition external comparison. Formal12=0/12 unchanged.
Source registry/reference follow-up is REFERENCE_STATUS.md; no invented formal
20stacks/sizes, no waivedMTT/ring/2–9/positions/ante/rake requirements.

## Resume / next shortest work
/workspace/joint-updates-run/{method}.sqlite:each completeepoch3/cursor0 with
complete1755eval accumulator. No training worker remains; do not rerun these.
Method identities in registration.json pin unchanged joint_updates.py/.cc/base
sources/game/cache. Prior main/warm/originalDB backups remain preserved.
Operator/controllers/rawlogs will be included in local recovery archive. No
AUTO-RESUME,independent restart,external persistent storage is configured.

Next: replace epsilon behavior-only reset with a justified regret-transfer or
conservative sequence-form update/averaging approach,validate on analytic games,
then require SAMEpopulation independentBR improvement before adopting. Alternating
updates need their own coherent fullpopulation protocol,not per-board preflop
updates. Complete formal provenance and independent richer-game/reference
calibration before normal range admission. Remaining release hoursUNKNOWN.

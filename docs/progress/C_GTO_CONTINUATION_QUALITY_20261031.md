# Restricted continuation-game quality acceptance
Base public b977f99cdd02b8372ff7ecddebd66d392f6e418a, clean shadowefdc0ef.
Acceptance before implementation: exact chance/card-removal weighted Bayesian
4-arm type game; own/public information only; synchronous full-information
regrets with uniform time-average strategies; exact own-type BR, NashConv and
external-regret bound cross-check. Never maximize separately by opponent type.
Legacy continuation_learning.py remains immutable to preserve prior evidence:
its sample/visit-weighted updates are descriptive online contextual learning,
not a proven full-sweep Bayesian-game NashConv convergence certificate.
Train boards: (48,21,3),(35,31,27),equal research weights NOT real flop chance.
Predeclared HELDOUT boards: (44,25,2),(40,41,7),(36,32,29),(20,12,4).
No heldout selection/tuning. Own key intentionally abstracts public boards;
this is a restricted signal/type game,not full public-board perfect-information
strategy space. Seeds17/29 control initialization only; exact evaluation has no
sampling seed/error. Fixed-opponent BR plus convergence curves; conditional
selfplay improvements are NOT external GTO improvements. Formal0/12 unchanged.
Optional research-only leaf export must preserve SB/BB sign, chips/BB basis,
class-pair conditional probabilities and actual flop; chosen equal board weights
must NEVER be passed as real-deal flop chance to existing CFR.

## Local evidence
9new tests PASS: analytic zero-sum game,information-constrained BR,bruteforce
own-type policies,first-two-sweep uniform average,regret bound/scale/seed,
exact posterior marginal vs blocker inclusion-exclusion,independent existing
world evaluator,leaf sign/order/chance reconciliation,fixed-opponent/heldout
read-only behavior. No oldsource/assertions/golden data changed.
Train2joint games*2seeds: restrictedNashConv at100000 is
vs3bet .002681238/.002684108BB;vs4bet .004098525/.004050761BB.
NashConv/2 is restricted exploitability ONLY. Positive externalregret upper
bound agrees within numerical guard1e-7BB. Standardized full sweeps now supply
a limited-game regret/convergence basis absent from prior selfplay EV.
6boards*2stages exactly evaluated.4heldout boards never update/select policy.
Heldout NashConv .398484..3.048306BB,unknown type mass0: generalization FAIL,
not a normalGTO release. Exact evaluation sampling error0 (previous heldout
2048draw halfwidth4.307771BB eliminated). Arithmetic/model/external separated.
6fixed opponents,eachseat BR;24researchleaf exports reconcile weightedEV and
SBchip sign/transposition. Cells with0compatible combos markedunreachable.
Actual-flop hook is not connected to oldCFR; true boardchance integration
remainsBLOCKED by incomplete continuation/board support. No user approval needed
for next safe research step. FrozenPi/8ranges/demo/HU1BB/2..9 unchanged.
## Resume
Check publicHEAD,dirty state,rawpush+PR CI. ReadQA README/results/convergence.svg.
Newtests: python -B -m unittest tests.test_continuation_game -v
Newdata: python -B -m gto.abstract.continuation_quality --build-dir /tmp/quality
 --output /tmp/quality.json
Next: predeclare a NEW train/validation/test board split before any new tuning,
expand public texture features/board support,validate broader own-type responses
and leaf true-chance integration. Never reuse these4testboards as untouched test
if training on them. Formal0/12,full-game external accuracyUNKNOWN.
No production/main/Storage/Vercel/otherPR/SSO/fees changes. AUTO-RESUME/restartnone.

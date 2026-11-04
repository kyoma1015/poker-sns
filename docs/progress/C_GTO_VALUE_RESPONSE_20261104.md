# C GTO conditional value and bounded local response

Before fitting: public baseline e50a570dcb78e102b179052755f327ecdc2fc23e, original shadow7d3b374 retained at /workspace/poker-sns. New /workspace/poker-gto-value contains exact public commit object SHA-verified against authenticated GitHub metadata; same tree, shallow public boundary, source object alternates remain at original checkout. No force/reset/public rewrite.

Preregistered21train/7validation/7final across7structure strata;107used suit-orbits excluded. Trips exhausted in historical studies; no formal scope change. Seeds11801/12809/13829, teacher initialization31/43,10000sweeps.7candidates: probability KNN9, conditional EV softmax/greedy, positive regret, bounded local response64/512/4096. Conditional values use only own information after integrating opponent chance. Local solver is explicitly transductive board-specific planning, not zero-shot transfer.

Acceptance before implementation: exact gain/conditional EV conservation; value targets normalized by own chance; no opponent-card decision input; independent train/validation/final; validation-only stage-wise noninferiority constrained selection; frozen final. Final5criteria:20%mean gain, global worst nonincrease, vs3bet mean/worst noninferiority, vs4bet same, absolute worstNC<=0.1. Formal0/12 unchanged pending evidence. External NOT PERFORMED, real-game error UNKNOWN.

Only new GTO modules/tests/docs and active GTO workflow. Preserve frozen CFR,8ranges,staticdemo,HU1BB/2..9. Old6SUCCESS recognized, no rerun. New changes require new-head CI.

Resume: implement conditional targets and separate warm response, tests; select validation only; commit lock before final; save negative outcomes and fixed-profile metrics; push FF only to PR120; inspect new CI. Keep PASS total UNKNOWN if logs unavailable. No prod/main/Storage/SSO/otherPR/fees. AUTO-RESUME absent.

## Completed research result
Validation selected fixed response4096; simple EV/regret transfer candidates all regressed. Lock commit precedes final. Final response meanNC0.005778591/max0.032241192; matched probability0.951012749/max6.589049507; prior frozen probability SAMEnewcases0.703352162/max3.053405532. vs3bet response mean/max0.007891537/0.032241192;vs4bet0.003665646/0.008136443.5/5research criteria PASS and28/28contexts below0.1; this is exact-board bounded local solving, NOT zero-shot transfer or fullNLHE. Formal0/12unchanged.

Fixed-opponent conditional-EV predictor final MAE1.547539BB,max30.480298 remains poor. Response uses current exact-game utilities instead. Numerical guard1e-7,samplingerror0fixedconditions,real-game errorUNKNOWN,externalNOT PERFORMED.

14localtests PASS; new-head CI pending when result commit written. Readonly14validation timing contexts reproduce lockedmetrics1e-12; matrix median1.007s, features/game0.273s, cold NN0.688s, response+certificate0.143s. Observed machine cost only.

Resume READMEcommands with fresh output paths. Next candidate requires new preregistration,142used suit-orbits excluded. Do not retune on final or claim new zero-shot quality. Preserve original source checkout because working clone uses alternates. CI aggregate countUNKNOWN on log timeout; no estimates. No autoresume.

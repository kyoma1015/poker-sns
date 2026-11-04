# C GTO conditional value and bounded local response

Before fitting: public baseline e50a570dcb78e102b179052755f327ecdc2fc23e, original shadow7d3b374 retained at /workspace/poker-sns. New /workspace/poker-gto-value contains exact public commit object SHA-verified against authenticated GitHub metadata; same tree, shallow public boundary, source object alternates remain at original checkout. No force/reset/public rewrite.

Preregistered21train/7validation/7final across7structure strata;107used suit-orbits excluded. Trips exhausted in historical studies; no formal scope change. Seeds11801/12809/13829, teacher initialization31/43,10000sweeps.7candidates: probability KNN9, conditional EV softmax/greedy, positive regret, bounded local response64/512/4096. Conditional values use only own information after integrating opponent chance. Local solver is explicitly transductive board-specific planning, not zero-shot transfer.

Acceptance before implementation: exact gain/conditional EV conservation; value targets normalized by own chance; no opponent-card decision input; independent train/validation/final; validation-only stage-wise noninferiority constrained selection; frozen final. Final5criteria:20%mean gain, global worst nonincrease, vs3bet mean/worst noninferiority, vs4bet same, absolute worstNC<=0.1. Formal0/12 unchanged pending evidence. External NOT PERFORMED, real-game error UNKNOWN.

Only new GTO modules/tests/docs and active GTO workflow. Preserve frozen CFR,8ranges,staticdemo,HU1BB/2..9. Old6SUCCESS recognized, no rerun. New changes require new-head CI.

Resume: implement conditional targets and separate warm response, tests; select validation only; commit lock before final; save negative outcomes and fixed-profile metrics; push FF only to PR120; inspect new CI. Keep PASS total UNKNOWN if logs unavailable. No prod/main/Storage/SSO/otherPR/fees. AUTO-RESUME absent.

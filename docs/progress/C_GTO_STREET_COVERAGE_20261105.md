# C GTO extensive action tree and true-chance coverage

Base/local75f4e46dbbf534fce609ab26f371fbf03501f07c,clean; existing6SUCCESS/57researchPASS recognized,no rerun. Work /workspace/poker-gto-value,preserve /workspace/poker-sns object source.

Preregister before computation:177used suit-orbits excluded for fresh14train/7validation/7final;18899/19913/20921. Half-pot full legal-response finite tree, then1/3,1/2,3/4sizes; one legal raise limit, no later betting. Public-history-specific behavioral decisions avoid tying responses across sizes. New CFR,notoriginal frozenCFR. Candidate512/2048/8192 selected ONLYvalidation; final once plus deterministicCIreplay. Priorfrozen31/43,not MC evaluation seeds.

Population evaluator: actual frozen boardchance,8strata,pre-fixed draws with replacement,32/64/128checkpoints perstage. Allpopulation boards may include knownboards but NOT new unseen tests; never select on their outcomes. Uniform-init512CFR gives exact restricted-gameBR brackets regardless convergence. StratifiedHoeffding family99% over2stages×3checkpoints×4tails. Profile[-50,50]; restricted gamevalue[-pot/2,pot/2] checkfoldsafe bounds. Numericalguardseparate,realgame errorUNKNOWN. Compare exactcomputedprobabilitycoverage,target0.003,with statistical full-population inference,not100%exactcoverage. Bounds/unknown mass explicit. Resume via guardedatomiccache;no autonomous restart.

Finalcriteria bothgamesmeanNC<=.05/max<=.1,referenceBRgain50% vslegacy5,nonincreasedworst. PopulationgameVintervalwidth<=halfanalyticrange andprofilewidth<=50BB,failurespreserved. EmptyCIintersectionFAIL,no redraw.

Externalreference public-source availability/spec investigation only; no paid acquisition/authbypass/unlicenseddata reuse. No frozenCFR/8ranges1352/HU1BB/2..9/staticdemo edits. No main/prodDB/Storage/Vercel/otherPR/SSO/fees. Formal0/12,externalunverified,realgameerrorUNKNOWN.

Next: implement newpublictreeCFR+private-infoBR,legacyplanlift,probabilitystratified evaluator/cache;independenttests;freezevalidationchoice;final;population;commit/pushoneFF and inspect newCI. PASSaggregateUNKNOWN on logs timeout.

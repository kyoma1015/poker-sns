# C GTO extensive action tree and true-chance coverage

Base/local75f4e46dbbf534fce609ab26f371fbf03501f07c,clean; existing6SUCCESS/57researchPASS recognized,no rerun. Work /workspace/poker-gto-value,preserve /workspace/poker-sns object source.

Preregister before computation:177used suit-orbits excluded for fresh14train/7validation/7final;18899/19913/20921. Half-pot full legal-response finite tree, then1/3,1/2,3/4sizes; one legal raise limit, no later betting. Public-history-specific behavioral decisions avoid tying responses across sizes. New CFR,notoriginal frozenCFR. Candidate512/2048/8192 selected ONLYvalidation; final once plus deterministicCIreplay. Priorfrozen31/43,not MC evaluation seeds.

Population evaluator: actual frozen boardchance,8strata,pre-fixed draws with replacement,32/64/128checkpoints perstage. Allpopulation boards may include knownboards but NOT new unseen tests; never select on their outcomes. Uniform-init512CFR gives exact restricted-gameBR brackets regardless convergence. StratifiedHoeffding family99% over2stages×3checkpoints×4tails. Profile[-50,50]; restricted gamevalue[-pot/2,pot/2] checkfoldsafe bounds. Numericalguardseparate,realgame errorUNKNOWN. Compare exactcomputedprobabilitycoverage,target0.003,with statistical full-population inference,not100%exactcoverage. Bounds/unknown mass explicit. Resume via guardedatomiccache;no autonomous restart.

Finalcriteria bothgamesmeanNC<=.05/max<=.1,referenceBRgain50% vslegacy5,nonincreasedworst. PopulationgameVintervalwidth<=halfanalyticrange andprofilewidth<=50BB,failurespreserved. EmptyCIintersectionFAIL,no redraw.

Externalreference public-source availability/spec investigation only; no paid acquisition/authbypass/unlicenseddata reuse. No frozenCFR/8ranges1352/HU1BB/2..9/staticdemo edits. No main/prodDB/Storage/Vercel/otherPR/SSO/fees. Formal0/12,externalunverified,realgameerrorUNKNOWN.

Next: implement newpublictreeCFR+private-infoBR,legacyplanlift,probabilitystratified evaluator/cache;independenttests;freezevalidationchoice;final;population;commit/pushoneFF and inspect newCI. PASSaggregateUNKNOWN on logs timeout.

Completed numerical batch:14new core tests+2root tests and57old regressions PASS=73distinct tests. One unused test import initially failed,removed,affected tests rerun PASS. Local prereg/code/selection commit dates in local-freeze-ledger.json; public API objects recreated later, not externally trusted pre-registration timestamps. No final retuning.

Validation selected2048(overall mean.037141430/max.085426178); final half mean.022473059/max.039352607, multi.047961653/.087937462.56/56 contexts below.1,4/4registered research criteria PASS; NOT formal acceptance. On SAMEnewgames legacy4 NC means2.772126063/4.828093568,legacy5.732481823/2.471998388. Half-policy extended to multi mean1.848613621/max3.860065032. Legacy normal-form/behavior profile consistency max1.421085e-14BB.

Population uniform512,128unique physical boards perstage: actualP .005845229705/.005869225252 (~.585%,not100%). All8registered probability/integration gates PASS, no empty intersections. 99%simultaneous restricted-game V bounds vs3[-5.435229367,1.112933037],vs4[-15.920299107,-.810468370]BB. ProfileEV intervals[-19.946027468,15.617394277]/[-26.154137686,9.404661185]. LocalBRwidth .146746327/.175135096 separate from sampling and unknown realgame error. Uncomputed profile contributions still ±49.707738515/±49.706538737BB deterministically. Statistical integration is not complete exactEVcoverage.

Posthoc readonly root bookkeeping(no new fit/testboards): twoCALLprefixmass.0262877732,computedrootboardmass.0001537011183 (~.01537%),otherunresolvedCALLmass.5625331508. Foldterm exact; rootSB interval[-28.687245232,28.500944718]BB for fixed preflop actions with new512continuations at twoleaves and otherCALLcontinuations bounded±50. NOT original frozen complete EV,notGTO. This identifies high-reach unresolved otherCALLs as a major blocker; never fill them with0.

Externalcode/library availability investigated3new public repositories; no matching authorized169frequency/EV reference acquired. Reuse prior provider audit, GTOBase free50BB candidate openbutfulltree/ante/EVbasis/exportpermissionunknown. External comparisonNOT PERFORMED, realgame errorUNKNOWN. Official0/12 unchanged; normalGTOadded0; eight researchranges/1352rows maintained.54protectedsha checks PASS.

Next: inspect new-head6CI,repair actual failures; do not manually rerun oldsuccessfulCI. Then preregister extension to high-reach limp/single-raised CALL histories,morelegalraises/later-street abstractions,with boardchance intervals and unchanged frozenpolicy. New unseen registry410suitorbits excluded including populationboards. Resume guardedcache /workspace/gto-street-population-cache and docs/qa/street-coverage-20261105/README.md. No autonomous restart. CI statusPENDING when this result commit is written; exact publicHEAD/CI receipt saved outside repo and PRaftercompletion.

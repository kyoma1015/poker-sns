# Legal-size / multiplayer release gate — 2026-11-24

Base d1ce78882afa9624d78cd48cdcfee3dc9f522e10, PR120 Open/Draft. Initial 8 CI families / 9 runs SUCCESS, attempt1, read-only. No successful CI manually rerun.

## Implemented, not formally accepted
One sparse native external-sampling CFR+ engine reuses the original State, pot ledger, ranker and corrected R/S. Full native action enumeration failed its bounded first-pair resource gate (148480 nodes,1.022s,0 updates). Generic pot-relative geometry completed4 pairs/.01772s/2014 rows; it supports minimum/full raises and .5/.75/1/1.25/1.5/2 pot-after-call fractions. Root10/99 actions (8/97 raises),89 omitted raises. 3.5BB and10.5BB arise from the general rule. Every actual public history has a distinct key; off-tree responses use legal own/public pot-odds priors, never fold filling or nearest-history aliases. Those priors are NOT verified GTO or safe resolving. All omitted-size error upper bounds UNKNOWN.

Both traverser updates use the same pre-update strategy, committed only after a complete pair. Independent tiny native tree checks regret/average expectations. Own-card/board prefixes split prior pair/set aliases; no opponent hole/future card is passed to decisions. Full real-world board/chance removal and original settlement retained. Fine keys improve separation but current trained postflop heldout reuse is almost zero; parent behavior dominates. No stable generalization/coverage improvement claim.

## Adopted evidence: hu-final only
Initial hu shared-tape conditional estimator and selection statistics are PRELIMINARY/WITHDRAWN as final evidence: action RNG and future resampling were not proven independent. Historical files and exact controller sources preserved. Final estimator uses independent upper64 action / lower64 future streams (regression checks identical action paths). Native learning kernel/checkpoints were unaffected. Final selection seed+1400000; final8192worlds17126301; discovery256worlds17126201; confirm32768worlds17126501. No final data used to select policies. Confidence allocation .0003 native / .0003 confirmation / .0004 jam EV sums .001.

Both seeds selected64 complete pairs, stopped at256 on selection deterioration; no longer training adopted. Training+selection+checkpoint15.087s/15.017s; peak RSS360140800/415133696 bytes. Selected rows53854/59240; regret-visited8202/10035; average-visited45847/49381. Preliminary raw working checkpoints156MiB losslessly gzip archived (~43MiB); duplicate compressed objects share relative symlinks with byte verification in checkpoint-dedup.json. Existing corrected checkpoints and research8 unchanged.

| Final independent evidence (BB, joint >=99.9% family confidence) | seed17120101 | seed17120102 |
|---|---:|---:|
| Policy digest | 4864081d387096007ed3db55b56bf50c496293e3f744dfc79e93142eed1e2984 | fd8d2219e1435433e6d8890baaea652c77f2972adff30848d82282bd86e012a7 |
| SB EV8192 | .033095 [-.795851,.862042] | .219269 [-.705630,1.144167] |
| New minus old EV, paired | -.133118 [-1.128207,.861972] | .020494 [-.929090,.970079] |
| Fresh32768 3.5BB gain | .361914 [-.010229,.734058] | .283927 [-.130988,.698842] |
| Old minus new 3.5BB gain, paired | 1.934079 [.866856,3.001302] | 1.924071 [.863710,2.984433] |
| Discovered omitted8BB gain, independent confirmation | .269517 [-.121823,.660858] | .208280 [-.219940,.636501] |
| 10.5BB gain8192 | .665452 [-.456338,1.787242] | .155206 [-.843999,1.154411] |
| River jam8192 | .246094 [-1.064800,1.556987] | -.516602 [-1.692365,.659162] |
| River nuts jam8192 | 0 [-.711808,.711808] | -.000122 [-.712540,.712296] |

Historical seed2 raw32768 gain2.132462 [1.286926,2.977997] is preserved, not directly paired with these new worlds. Fresh matched old seed2 gain2.207999 [1.288819,3.127178]. Known attack significantly reduced BOTH seeds; residual upper bounds positive, NOT eliminated. Overall EV improvement NOT significant. Root99-action discovery is not full BR. Current heldout native/reduced NashConv and full native BR upper UNKNOWN; old finite-action NashConv is not comparable to this expanded game. No physical100BB bound substituted.

Raw versus conditional payoff variance on1024 same-action CRN worlds140.095666 ->83.172140 /165.258715 ->90.445606 (~40.6%/45.3% lower). Exact990 flop /44 turn all-in runouts; preflop16 independent conditional boards. This reduces estimator variance, not model error.

Native selfplay monitoring: new trained/warm-only/default counts by street:
- seed1: pre5223/9329/270; flop4/5196/394; turn0/1876/963; river0/915/1100.
- seed2: pre4404/9067/107; flop1/6665/75; turn0/3446/107; river0/1840/145.
No parent or current row on1026/8192=12.5244% /177/8192=2.1606% paths. Current untrained path6897/8192 /6696/8192. New exact-history/refined keys differ from historical coarse counters; do NOT claim old .6226% improved from these. Warm-only is not new learning.

## 169 frequencies / action EV
Each seed stores169 legal action rows in5 contexts: RFI,vs3BB,vs3.5BB,vs10BB3bet,vs10.5BB3bet. Rows include warm/prior behavior, not all newly trained. All169 root fold EV exact-.5BB and jam EV intervals computed using exact1225 compatible opponent pairs and integrated opponent fold/call;32 independent conditional future boards/pair. Suit invariance explicitly checked. Max jam interval width .634138700016BB,2.52s/seed. Total676 measured root cells across both seeds;32786/33462 cells remain UNKNOWN, other contexts' EV also UNKNOWN. This is not formal EV PASS or complete all-action precision.

## Multiplayer
See multiplayer/README.md and independent oracle/results. Ordinary native fold/call/3BB open/10BB3bet/short/full shove now optimized in3-player finite4-world game with shared own/public infosets; postflop check/call continuation explicitly restricted. Independent full path oracle max error3.56e-15. Sum legal unilateral BR gains7.243827 ->.344938(8) ->.023738946(32); no unconditional multiplayer convergence theorem claimed. Side pot/refund/BBA/rake/unequal stacks/all seats replay tested.6max >20000nodes (9.032s,~75MB);9max contains this subtree, >20000 lower bound. Incomplete builds retained as failures, no partial strategies admitted. Next requires bounded multiway sampling with correct N-player reach/average updates, not copying HU average formula.

## Release and restart
Formal0/12 unchanged, verified RFI0 /3bet0, ordinary registry0. acceptance.json lists each gap/next step. Existing8 remain BLOCKED_UNVERIFIED. Full2..9/multi-stack/positions/EV/ante-rake/unequal-stack release scope unchanged, HU50 research only. Formal20stack/mode/sizing/ante/rake specifics PENDING approval, not silently adopted. Existing Git checkpoint bytes reused. Old-session non-Git research DB/ZIP cannot be recovered from this environment; not claimed recovered.

Build: python -B -m gto.qualification.sparse_solver --build /tmp/sparse-build --native-build /tmp/poker-public-response-build
Restore manually: first gto.qualification.build.load(native_build) to register pokerid_rules; module=sparse_solver.load(library); w,origin=sparse_solver.warm(module,seed); q=sparse_solver.Solver(module,w,origin,seed+1100000); sparse_study.archive_restore(q,Path('docs/qa/legal-size-20261124/hu-final')/str(seed)/'best'). Check freeze.json digest and checkpoint.json identity first. Gzip archives and relative symlinks are lossless; decompression hash checked. Same source AND binary required; different compiler/build identity requires explicit revalidation/new digest. No automatic restart service claimed. R/S/RNG bit-exact save/restore regression exists. All final values/histograms/world tapes and source identities persisted. No production/DB/Storage/UI/deploy/merge/SSO/billing changes.

Next: use independent discovery to add worst omitted sizes through a generic adaptive support rule and retrain matching downstream histories; improve strength abstraction sharing without hiding public action history; retain fresh final sets and stop non-improving seeds. Prove native BR/actionEV/model-error bounds before registry, while extending3-player sampling then6/9. No formal condition relaxed.

Local regression command is the exact unittest module list in .github/workflows/gto-native-qualification.yml:137PASS/40.208s before adding short-all-in case; focused new case1PASS/17.949s,138 distinct cases total. No TS/UI change; npm build/lint/browser not run locally. Actual selected checkpoint+RNG resume proven bothseeds,1.733s/1.618s; repeated next update identical binary hash, originals unchanged (resume.json). No automatic service.

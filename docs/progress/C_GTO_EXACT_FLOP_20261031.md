# Exact fixed-flop integration and independent continuation research
Base afc03a14dcc8783692b6634e74aba6ea37dcc604. Existing frozen strategies,
conditional32draw results and research demo remain immutable.
Acceptance: compare every990runout on selected concrete pairs to existing native
exact(); validate posterior against Python enumeration and full-pair counts;
finite exact weighted EV across all169classes; no hole/runout sample error;
independent old-MC seeds compared with exact truth and valid confidence intervals.
Do not confuse numerical guards,model approximation and external GTO deviations.
Learning interface sees only own/public observations. Train/eval data and seeds
must be disjoint. No full-game equilibrium claim from self-play.
Method to investigate: cache rank(own holes,flop,turn,river),then compare opponents
using integer win/tie counts. This avoids re-ranking the same7cards for every
opponent and may permit COMPLETE hole enumeration instead of more MC iterations.

## Implemented and locally verified
8new tests PASS, with every990 cached outcome checked against existing exact()
on selected concrete holes, all169posterior masses checked against Python,
AA/KQo/76s controller sums checked independently for BOTH stages, seat-exchange
integer identity, own-observation policy and disjoint unordered train/test pairs.
Initial mixture-unit example had a betting opponent that made parameters linear;
corrected the example to a checking/raising opponent to test action correlation.
No production or original engine/test assertion was weakened.
Exact4conditions/676rows, hole/runout sampling errors0, arithmetic guard1e-8BB.
8independent-MC checks all contain exacttruth,original4intervals also contain it;
finite empirical check NOT99%calibration proof. Benchmark full4conditions
2.377625s versus old32draw4condition equivalent4.540863s, compilation excluded.
Separate learner:4whole-plan arms, train1024worlds*12epochs,heldout2048worlds,
seeds17/29. Unorderedhole+flop hashsplit prevents swapped-seat leakage.
Policy observes own/public only. No full-game convergence or external reference.
Frozen policies, previous results,UI/demo unchanged; formal0/12.
## CI / resume
New gto-exact-flop workflow runs8newtests and rebuilds exact data/MCseedchecks/
learner reports with strict1e-12+sourcehash comparison. Benchmarks not compared.
Check actual publicHEAD and raw actions/runs (push+PR) before continuing.
Reproduce commands in docs/qa/exact-flop-20261031/README.md.
Next: heldout learning-gain/response certification within restricted game, more
flops with explicit budget, then independent matched real-game GTO reference.
Do not treat zero sampling error as zero model error or selfplay as externalGTO.
No production/main/Storage/Vercel/SSO/otherPR/fees changes. No owner decision.
AUTO-RESUME/independent restart absent.

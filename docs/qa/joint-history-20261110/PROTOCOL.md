# Small independent history/order/mixing study, before observing outcomes

Preserve all9bf6f06/frozen/all-population results. No long successful computation
rerun. Two tiny hidden-card/public-board games: existing audit game and same
card-removed chance with reversed equilibrium equity ordering. Enumerate both
players'64pure legal strategies; solve the resulting64x64zero-sum matrix with
installed scipy.optimize.linprog. This is an independent finite-game numerical
reference, not an external HU50BB reference. No new dependency or paid service.

Teacher:128simultaneousRM+linear iterations from the fixed audit behavioral
profile; retain ACTUAL R,S and schedule counter. Compare128additional updates:
1 simultaneousRM+linear with genuine R/S;
2 alternatingRM+linear with genuine R/S;
3 alternatingRM+linear with behavioral epsilon R reset but genuine S;
4 alternatingRM+linear with genuine R but S reset;
5 alternatingRM+linear with BOTH reset;
6 alternating dampedRM+(.25),genuine R/S, explicitly NOT standardCFR+.
Reset comparisons keep schedule offset128 so averaging weights do not confound
history factors. The offset is NOT claimed as retained regret/average history.
Actual inherited histories are separately labelled. Record checkpoints0/1/2/4/
8/16/32/64/128 with exact64pureBR,SB/BB gains,regret residual and every failure.

At each snapshot also compare baseline/current policies by sequence-form
realization mixing at fixedlambda0,.125,.25,.5,1. No pointwise-behavior mixing
claim. Exact BR is an optimization objective within this SAME small game, not a
holdout or real-game validation. Best-checkpoint/mixture selection records every
candidate and applies1e-9tie guard,keeping baseline on ties.

Acceptance for full-population deployment: numerical reference LP dualgap<=1e-8,
explicit pureBR and recurrence/realization-affinity/resume parity PASS; alternating
order's final restricted NC must be at most75%of simultaneous on BOTH games and
improve the initial baseline. Otherwise no new all1755training is authorized by
this protocol. Damped policies can be described only as research,not standardCFR+.
Even meeting this selection rule cannot establish fullHU50improvement orGTO.

Budget: at most30CPU minutes locally,2CPU/8GiB existing cgroup,no MonteCarlo,
no new secrets/production operations. No change to0.1BB population target or12
formal requirements. A positive full-population decision needs its own fixed
protocol/budget before any population run. No fabricated historical regrets.

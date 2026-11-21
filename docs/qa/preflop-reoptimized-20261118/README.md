# HU50 actual preflop reoptimization — BLOCKED_UNVERIFIED

One actual preflop policy-iteration update, not the previous fixed B frequencies.
No formal profile or ordinary registry admission. Formal 0/12, verified RFI=0,
3bet=0; old eight research candidates and all prior checkpoints preserved.

## Algorithm and evidence

`preflop_reopt.py` feeds full three-street public-range continuation payoff
matrices into the existing C++ 169-class CFR kernel (100 iterations). Eight
uniform public boards, exhaustive compatible physical private pairs, shared
public-history action coins, exact chance correction C(52,5)/C(48,5). Policy
receives only current board/public history/own bucket. Future board exclusion
is performed by the evaluator only, never the policy's range construction.
Card-overlapping private pairs are excluded. Short all-in/legal actions and
settlement reuse the protected reference/native engines. Completed kernel worlds
checkpointed atomically; incomplete world discarded, never filled with fold/zero.
NumPy 2.3.5 performs exact-index aggregation; floating numerical error unbounded.

Generation 39.274989 seconds, 8/8 boards, 100 CFR iterations, approximately 3 MiB
compressed evidence (100 MiB cap; 300-second generation cap). All model action
EVs/reach and full-tree frequencies saved in both strategy artifacts. Zero
probability omitted native actions and exact-history frozen fallback remain
explicitly unverified; the 3/10/50 BB training tree is not full-size qualification.

`range_reoptimized.json.gz`: preflop digest
521f4fa4b09ab8f3c08e5a1fbf03990453f0df4db633d88abbbd6ea7095be85d;
combined current-range policy digest
65b9610c35ce044a3c3ba5895ab92a908da686c8eaeca64699efc1ee0fe7fb0d.
3,074 flat strategy elements differ from old B. Changed hands: RFI 166/169,
vs-open 169/169, vs3bet 159/169; every stage exports 169 rows (also vs4bet).
`native-frequencies.json.gz` explicitly includes every native legal action
(including omitted training sizes with zero frequency) for169x3contexts.
Matched passive control uses identical boards/chance/CFR/seed/build, so changes
from Monte Carlo samples can be distinguished from continuation-payoff changes.
Against that control, changed hands 156/166/148 respectively.

Training payoffs use old-chart posterior ranges. Runtime correctly reconstructs
ranges from the NEW frequencies. This is one policy-iteration step, not a coupled
fixed point: anchor/range coupling error UNKNOWN. No convergence claim.

## Independent native holdout

`native-holdout.json` + checkpoint: fresh seed17118302, 256 full root worlds,
2,048 native paths, 41.297988 seconds, identical decks/tapes for all comparisons.
Identity records source/native binary hashes, every world and all four digests.
Family confidence99.9% across11 intervals. New SB EV .169921875BB;
old B -.103515625; prior fixed-chart Range .130859375;
matched-passive-kernel frequencies with current Range .404296875.
Paired new-oldB +.2734375BB CI[-21.053944,21.600819];
new-priorRange +.0390625[-21.202932,21.281057];
new-control -.234375[-22.147007,21.678257]. No significant improvement.
Learning expansion gate FALSE: no longer training run authorized by these data.

Legal unilateral deviation gains (BB), same new digest/worlds:
3.5BB open -2.812500[-31.617461,25.992461];
10.5BB 3bet +.894531[-19.769225,21.558287];
BB river jam -.386719[-20.749030,19.975593];
general river nuts 0[-18.298453,18.298453]. The nuts probe made34eligible queries but zero nut-trigger jams on these worlds
(`river-probe-coverage.json`, exact same-payoff replay); it did not exercise the
rare known attack. Zero empirical gain does not prove
no vulnerability; old conditional-event mass cannot be transferred to new chart.
Independent finite-probe BR/NashConv lower bound0 is uninformative.
Full native BR upper, NashConv point/upper, omitted-size error and uniform
continuation/range-coupling error UNKNOWN. No trivial physical BR cap substituted.

Restricted sampled-kernel metrics ONLY: SB EV .398381261, BR maxSB .450059063,
BR minSB .371507139, NashConv .078551924BB. These are not independent native
BR results or full-game qualification. Native root EV interval width24.677452BB
(n256); cannot compare to old different-policy/sample-count widths as improvement.
Selected-action conditional EV: all169 x3contexts x3actions =1,521 entries,
3,042 independent native paths with two samples per entry,84.551421seconds.
Maximum simultaneous interval width100BB; precision FAIL. These measurements
are separate from root-weighted EV;
full legal-action EV precision remains UNKNOWN and precision gate unpassed.

## Verification / resume

85 qualification regression tests PASS (4 new): exact small-deck chance
correction, exact card-removal aggregation, scalar full-street native oracle
replay in two pots, mixture sampling matches existing policy probabilities.
Existing A/B/frozen/river/range tests retained. `resume-check.json`: replaying the
8-world kernel checkpoint with zero new worlds produces identical two digests.
No npm/build/lint/browser QA locally: no app/TS/UI change. New automatic CI is
recorded separately in PR120; no successful workflow manually rerun.

```sh
python -B -m gto.qualification.preflop_reopt --build /tmp/poker-public-response-build --library /tmp/range-continuation-build/range.so --out docs/qa/preflop-reoptimized-20261118 --worlds 8 --seconds 300 --resume
python -B -m gto.qualification.preflop_reopt_eval --build /tmp/poker-public-response-build --library /tmp/range-continuation-build/range.so --out docs/qa/preflop-reoptimized-20261118
python -B -m gto.qualification.preflop_reopt_actions --build /tmp/poker-public-response-build --library /tmp/range-continuation-build/range.so --out docs/qa/preflop-reoptimized-20261118 --resume
```

Paths under /tmp are local builds, not Git-recovered binary bytes. On a new
machine rebuild native and range libraries with the existing build modules;
compare build/source identities before any resume. No automatic resume service.
Git contains compressed kernel and strategy bytes; other old-session ZIP/DB files
outside accessible workspace have not been recovered. Current prior committed
artifacts and local build paths accessible; no deletion or overwriting old QA.

Next: quantify anchored/current-range payoff drift on matched holdout worlds,
then a coupled update only if native improvement gate passes; increase independent
precision efficiently and obtain omitted-size/uniform-error/full-BR bounds before
certificate/registry/search admission. No UI work. Formal A/B/C specs remain
PENDING: 20-stack profiles/MTT vs ring/ante-rake, chip size/all legal sizes,
minimal qualification and thresholds; see existing release proposal. None adopted.

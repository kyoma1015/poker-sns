# Exact fixed-flop model integration and separate continuation research

Base afc03a14; frozen CFR policies and old32draw results are unchanged.
Same HU50BB,ante/rake0,hero CALL history and two predeclared public flops.
Every compatible concrete hole assignment and all990runouts are integrated.
1176 legal own pairs,1271256 ordered matchups/flop. Swap symmetry needs
635628 unordered matchups/flop. Two flops share cached results across stages.
Integer win/tie counts; extended-precision weighted sums. Sampling error0.

|stage|flop IDs|old BB|new BB|delta BB|previous99% delta interval|
|---|---|---:|---:|---:|---|
|vs_3bet|[48, 21, 3]|-3.097294278958|-9.594083653738|-6.496789374780|[-24.511565708639637, 9.622310852222235]|
|vs_3bet|[35, 31, 27]|0.200072418460|-0.275028510548|-0.475100929008|[-16.97485046417767, 16.488991784840486]|
|vs_4bet|[48, 21, 3]|-5.761183338696|-7.560177859328|-1.798994520632|[-27.765235419700918, 23.972663182593248]|
|vs_4bet|[35, 31, 27]|-1.567076951336|-0.228388201935|1.338688749401|[-25.16658526851547, 28.5610511849272]|

Current sampling half-width0. Arithmetic guard +/-1e-8BB is separate,
NOT a statistical99% confidence interval. It conservatively dominates
binary rounding with >=64bit mantissa long-double sums (compile-time check),
<=12972 terms/class (12*C(47,2)), finite positive reach weights, values
bounded by50BB, and final correctly-rounded binary64 exports. Normalization
uses nonnegative mass; signed numerator cancellation is bounded by sumabs.
No underflow/extreme arbitrary external weights are used.

Old model: existing fixed card-controller on this flop. New: same fixed
experimental raise/call as prior study. Different signs are MODEL differences,
NOT GTO accuracy gains. Real-game approximation and external GTO UNKNOWN.

## Method and cost comparison
Previous method ALREADY had169strata,exact990 Rao-Blackwell runouts and common
random worlds for old/new differences. More samples/opponent strata/selective
enumeration retain residual MC error. Cached rank(own-hole,runout) makes FULL
hole enumeration feasible,so no selective tail estimate is needed here.
Local algorithm wall time: all4exact conditions 2.377625s (compile excluded);
old32draw estimator equivalent4conditions 4.540863s (two seed runs averaged).
Not a cross-machine performance guarantee. Individual times in benchmark-local.json.

## Independent seeds and interval checks
Two NEW MC seeds per condition,8checks. Exact truth inside8/8old-method99%
intervals; original4prior intervals also contain truth. This finite count is
NOT empirical proof of99%calibration or unbiasedness. Exact reference itself
has no PRNG seed and no sampling bias within the frozen abstraction.
MC error vs exact across new checks spans [-1.0280832587686723, 1.01413481095117].

## Separate continuation learning
4 whole-plan arms, own/public features ONLY. Do not average Policy parameters:
a mixture over complete plans preserves within-hand correlation. Contextual
normal-form regret matching is NOT full-game CFR, exploitability,or equilibrium
certification. Original frozen CFR arrays are never updated.
Train1024worlds,12epochs; heldout2048worlds. Seeds17/29 and evaluation seeds
900018/900030. SHA256(unordered concrete holes,flop)%5 splits train!=0/test==0;
swapped seats cannot leak the same matchup. Same public flops are shared;
unseen-flop generalization is NOT tested. Both learned seeds retained,not
selected by evaluation payoff. Dataset/policy/provenance hashes saved.
Heldout self-play intervals apply only to frozen plans on this heldout
partition,not external GTO or in-sample train results. Training results have
NO confidence guarantee. No external reference used.

Reproduce:
python -B -m unittest tests.test_flop_exact -v
python -B -m gto.abstract.flop_exact_study --build-dir /tmp/exact --output /tmp/exact.json --benchmark /tmp/benchmark.json
Compare results.json with gto.abstract.verify_export (1e-12 + source identity).
Runtime benchmark is intentionally NOT part of deterministic golden comparison.
Formal0/12; no UI/range/production publication.

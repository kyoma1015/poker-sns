# Active CF refinement / conditional EV — release remains BLOCKED

Base5ca70afcb80e8b5348bffbe1b5d8471a90aabc55. Code0e6a9e6a8a34d4dc2e9ccd4839af3b872d8179f4.
HU50 is a milestone, not initial release. No specification adoption, registry
admission/publication, production/SQL/main/deploy/SSO/billing/force/destructive work.
Original8candidates/frozen/HU1BB/allCP/rawJSON4 are preserved. Formal0/12/RFI0/3bet0.

## Actual solver changes

`cf_refine.py` ranks causal made-category/primary rank/draw/suit/blocker features
by frozen-policy CF Jensen residuals, with exact private card removal/opponent
reach. Current on-policy reach is recorded separately; unreachable-under-sigma
counterfactual paths are not silently discarded. These LOCAL scores are not
additive global BR bounds. All earlier own selected observations remain in keys.

New selected8 coarse cells/seed split their causal features. Unchanged row R/A
history is copied exactly; newly appended fine rows startR/A0 with frozen parent
behavior. No historical fine CF regrets/average mass are invented. Unseen fine
states delegate to the actual previous policy instead of a new uniform prior.
The sparse kernel,13-stratum public chance/private-vector integration remain.
Native initial128world paired behavior equality and same-bank finite physicalBR
identity are checked. New-row resets mean even matched-update differences are
not a pure causal estimate of information alone; a reset-only control is needed
before such a claim. No independent final data selected these split priorities.

## Selection controls: do not confuse more updates with more information

Selection catalog17160101+seed, independent of training chance. Budgets90/180
pureCPU seconds perarm, current2CPU/8GiB, one learner at a time.

| seed | parent fineNC |180CPU control t/fineNC |refined t/fineNC |same-update control fineNC |
|---|---:|---:|---:|---:|
|17120101|3.880013180|84 /3.649762342|86 /3.628823575|3.629758527|
|17120102|4.126642569|84 /3.987307696|87 /3.961703792|3.962324677|

The equal-CPU apparent gain .020939/.025604BB shrinks to .000935/.000621BB when
updates/public draw prefixes match exactly. Most apparent improvement came from
more updates. This is not a material/global precision breakthrough or releasePASS.
Original full64CPs and new initial/last/matched controls are retained independently.
Both unchanged history and new-row cold starts are explicit in checkpoint metadata.
Final candidate is predeclared refined last, never selected from final outcomes.

## Independent chance/BR scope

Raw fine BR in a13board catalog can exploit suit-specific sampling-law artifacts.
`symmetry_br.py` evaluates its suit/flop-order symmetrized law via observable orbit
keys, without144x world storage. For invariant sigma, an invariant optimal BR
exists in that symmetrized law. An independent regression explicitly enumerates
all24suit×6flop-order images and matches EV/bothBR/NC to1e-9.
This is a DIFFERENT explicitly symmetrized finite chance law, NOT uniform52.
Both raw/symmetric metrics remain separate. The legacy5ca final law is used only
to diagnose that OLD policy/law, never to select a new candidate. Future-runout
aliasing of a small catalog is still possible; fullchance error remainsUNKNOWN.

`native_tree_bound.py` replays every offered native action and checks all terminal
loss/tie/win payoff bases against the native rules ledger. Mispriced rewards or
nonterminal cut leaves invalidate the proof. Fulllegal omissions are enumerated.
Covered terminal payoff error0 is scoped to the covered HU chipEV tree; it is
not a uniform full-native continuation/size/chance certificate. Missing global
proofs returnUNKNOWN, not a100BB physical convergence surrogate.

## Size support

`adaptive_support.expand` ranks development CF residual inputs, checks actual
native legal raises, inserts only within a public-node budget, and builds all
corresponding downstream responses in the same private-vector CFR game. The
regression expands root12→13/99, joint-updates4.5BB and subsequent response nodes,
and verifies budget rejection. Residual fixture inputs are synthetic/test-only.
Main research policies remain12/99; no size-safety claim or formal sizing choice.
All87 root omissions and fullnative BR/NC upper remainUNKNOWN.

## EV estimator

`range_ev_core.cc` reuses the frozen card evaluator. It samples opponent pairs
from the exact card-removed same-policy conditional caller distribution and
uniform legal runouts. Policy code sees neither opponent cards nor futureboard.
The estimator integrates fold probability exactly. Dyadic, predetermined sample
checkpoints spend delta/[2k(k+1)] separately on empirical-Bernstein and Hoeffding;
selecting the narrower interval is union-valid. Sample variance is upper-bounded
by n*mean*(1-mean)/(n-1) for[0,1] outcomes, including ties. CDF quantization error
and numerical slack are included. Fixed-board weighted straight/tie/removal
oracles pass. A7 numerical proposal precision is NOT formal acceptance.
Existing per-digest Fold507/Jam97/111 and all older EV evidence remain separate.

## Multiplayer

New root-quantile external sampler preserves the combined uniform proposal law,
old N counterfactual corrections, lazy averages, all-seat information and card
removal. First root-owner traversal is not redundantly repeated. Exact3person
K4 path gradient/average and RNG nextstep oracles pass. Fixed-policy32trial raw
variance/CPU pilot worsens efficiency in both seeds; no larger learning adopted.
6/9 old strategies/cap/rollback are protected, not relabeled improved.

The9max cap is chiefly distinct public histories:14,471/14,353 public states for
19,930/19,804 rows. Exact own-card factoring saves only~30% state-key text there
(~60% at6max), not enough to solve branching. Cap was not merely raised. No
multiway general Nash convergence claim. Exact3 reference .023738946 preserved.

## Lossless capacity and recovery

`refine_checkpoint.py` XORs new arrays against aligned, immutable parent arrays;
new fine cells align to zero. Every shard and reconstructed array hasSHA256.
Unchanged prefix keys are validated; tamper/source/build mismatch is rejected.
All6 real checkpoints reproduce next fresh RNG/R/A/visits exactly.
Same-array/same4MBchunk/zstdlevel1 comparison: full117,867,992/114,900,392 bytes,
XOR66,751,619/66,118,067 bytes:43.37%/42.46% smaller additional array payload.
Parent and metadata costs are separate. Historical1.63GB was NOT deleted or
reduced. Large new raw ranking JSONs remain locally, with byte-identical zstd
archives (<100MiB perblob) tracked; compression receipts pin reconstructed SHA.

Manual restore (not an automatic restart service):
```
old, parent, _, rules, native, module = cf_refine_study.make(seed)
q, metadata, rng = refine_checkpoint.restore(new_checkpoint, old)
parent.slim()
next_seed = rng.getrandbits(64)
next_q = cf_refine.next_bank(q, public_stream_batch.catalog(q.lib,next_seed),parent)
next_q.step()
```
Preserve rng/q on failed transactions, as the original driver does. Never overwrite
a checkpoint directory. Rebuild native/feature kernels and check source/build/
parent receipt/shard/array hashes first. Original5ca t64 is required; its ledger
alone cannot replace actual array bytes. Legacy external sessionDB/ZIP is not
accessible/recovered. For rerunning rank-driven studies, decompress each tracked
selection-rank.json.zst to its raw.json path and verify rank-compression.json.
Full initial release2–9players/20stacks/allpositions/modes/ante/rake/unequal stacks
is unchanged. Full quality solve/cachemiss resources areUNKNOWN, no completion ETA.

## Independent final results (not selection data)

Fresh catalog17160301+seed and32768 native worlds seed17160401. Family confidence
99.9%;200 preallocated native events across seeds. Final data must not select
future candidates. The refined candidate is NOT adopted: no consistent improvement
over matched-update controls. Actual policies remain root12/99,87 raises omitted.
The adaptive13/99 support is a unit/oracle prototype, not these native policies.

|seed|parent coarse/fine NC|matched coarse/fine NC|refined coarse/fine NC|
|---|---|---|---|
|17120101|3.962730/4.939796|3.740659/4.660290|3.747240/4.666208|
|17120102|3.614738/4.581315|3.501475/4.451020|3.505438/4.450455|

These are finite-catalog values, not complete native bounds. Suit-orbit BR
separately measures finite sampling-law artifacts; remaining finite fine/coarse
gaps must not be assumed uniform52 abstraction-error certificates.

Refined native SB EV .065338[-.265780,.396456] / .165983[-.166077,.498043]BB.
River-jam gain -.506393[-.943965,-.068822] / -.650970[-1.105847,-.196093]BB.
8BB gain -.919603[-1.417469,-.421736] / -.927802[-1.437924,-.417680]BB.
3.5BB -.259375[-.722347,.203596] / -.247882[-.714692,.218927];
10.5BB -.037064[-.296768,.222640] / -.023954[-.283649,.235740].
4.5/9.5BB positive point estimates have intervals containing zero: NOT safety.
Oldlast seed2 8BB issue remains unresolved; all paired comparisons in summary.

River average reuse including actual parent delegation99.6767/99.7626%;
regret98.8721/99.5387%. Reuse alone is not quality evidence. Each digest has
Fold507 exact and deduplicated Jam136/145 proposal-precision cells; formal0.
New caller-range estimator AA/KK/QQ vs10.5 uses empirical-Bernstein/Hoeffding
confidence spending with dyadic stopping, exact fold mass/card removal, CDF
quantization allowance. New halfwidths .03564/.04314/.04685 and
.04642/.03971/.04421BB, family budget split with original certificate.
All169 posterior hands remain nonzero in all three measured contexts.

Native terminal settlement oracle certifies represented terminal payoff basis
only. Omitted actions, full chance, continuation and information uniform error
remain UNKNOWN, hence complete native BR/NashConv upper UNKNOWN. No physical
100BB cap substituted. Formal0/12, RFI0,3bet0.

## Next concrete gate

Keep old selected t64 policies and all new last/matched states separate. Before
expanding refinement, use BR-continuation CF contributions rather than local
on-policy Jensen score, include reset-only controls, and validate fresh public
chance branching without finite-catalog future aliases. Require both-seed
matched-update independent fineBR improvement and native-size nonregression.
Next solver change must improve this failed gate rather than increasing volume.
All A1–A7 approvals remain pending, independent of technical blockers. Full
2–9player/20stack/all-position/mode/ante/rake/unequal-stack completion feasibility
on free resources remains UNKNOWN; no completion date or cachemiss claim.

Independent seed2 refined minus oldlast8BB gain +1.361353BB,99.9% interval[+.453991,+2.268716]: significant unresolved regression. Seed1 +.710477[-.269683,1.690638].

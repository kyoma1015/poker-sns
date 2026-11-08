# Full-population joint CFR and BR — research only

All1755 suit orbits /22100 physical flops are now computed for the SAME HU50
noante/norake preflop tree,9 matched branches,3 flop sizes/one raise/checkthrough
future model. This is full board coverage of a restricted game, NOT full NLHE.
Each player keeps own169class+own/publicflags and complete public history.
Opponent real cards are integrated in chance and never used as action keys.

The old28/22100 study is not extrapolated. Common preflop regrets are frozen
within each complete population sweep and updated ONCE from all weighted blocks.
Postflop rows are public-board specific. Exact independent BR first maximizes
postflop own observations, aggregates all boards' terminal counterfactual values,
then maximizes preflop by own class; no future-board preflop clairvoyance.

|Same full-population game/profile|Joint NashConv BB|SB net EV BB|
|---|---:|---:|
|Frozen small profile|0.932107153|0.030880258|
|Uniform initialization/epoch1 average|7.945002098|-0.199315201|
|Epoch2 average|5.582643558|-0.155725662|
|Epoch4 average|3.081906371|-0.057020265|

Uniform training improves against its own initialization but is WORSE than the
frozen profile. Predeclared0.1BB target FAIL. No model is admitted to ordinary UI.
At4epochs SB/BB feasible BR gains1.772423265/1.309483107BB are root reach weighted,
not the old CALL-conditioned3.244178/2.608232BB quantities. Positive regret bound
14.896357999BB remains above exact measured NashConv. These are exact finite
population point calculations; sampling error0, empirical arithmetic tolerance
1e-8BB, NOT a formal rounding-error proof or external GTO certificate.

## Independent consistency evidence

- Shared/chunked CFR regrets,average sums and BR match the old monolithic engine
  on an exact declared small population. Crash transaction rollback and resumed
  state digests match uninterrupted execution; identity/budget/missing support
  fail closed. Partial epochs cannot be evaluated.
- Frozen full-profile4563 actionEV values independently match the saved exact
  full class-pair oracle/core evaluator to1.78e-13BB; rootEV to5.17e-16BB.
- Across all28561classpairs and1755orbits, true blocker chance matches theoretical
  ordered-card class chance within2.20e-18. AllinEV matches the independent prior
  full oracle within3.12e-12BB; total joint mass1 within floating arithmetic.
- runtime/build fingerprints, full numeric moment ledger and completed epoch
  results are supplied. A checksum ledger is NOT the327MiB numeric cache itself;
  cache and1.5GiB checkpoints remain local and can be regenerated from source.

## Uncertainty / acceptance

Board chance evaluated100%,missing board chance0. This does NOT resolve omitted
actions or private information. Epoch4 nonallin showdown root mass22.404807% gives
a fixed-action future-value envelope[-11.065724886,11.339082482]BB. A newly allowed
raise can change earlier fold responses; this interval does not bound all omitted
flop actions. Added sizes,second raises,turn/river betting and own concrete suit
information beyond the chosen flags remain unvalidated. Universal payoff bounds
[-50,50]BB and full-action NashConv<=100BB remain the only safe general bounds.
The old64.449% conditional unknown mass is a different population/controller and
has not been claimed resolved. TT7.647099BB model sensitivity is tracked,notzeroed.

Formal0/12 unchanged:10PARTIAL/2BLOCKED(original20stacks/fullsizes). MTT/ring,
2–9players,positions,ante/rake remain required. Matched lawful external datasets0,
external comparison NOT PERFORMED, real-game approximation UNKNOWN. Existing
frozenCFR/research ranges/HU1BB/multiplayer regressions/UI/static demo unchanged.

WARMSTART.md registers a separate post-observation optimization trial using the
frozen profile as a tiny nonnegative regret prior. It is RUNNING at this snapshot;
no result is claimed. Uniform results are retained regardless of its outcome.

## Reproduction / resources

```
python -B -m unittest tests.test_joint_stream tests.test_joint_stream_study -v
python -B -m gto.abstract.joint_stream_cache --build /tmp/even --cache /tmp/moments --parity 0
python -B -m gto.abstract.joint_stream_cache --build /tmp/odd --cache /tmp/moments --parity 1
python -B -m gto.abstract.joint_stream_study --root /tmp/population --cache /tmp/moments --seconds 3600
```

Cache generator parity workers may run concurrently. Only ONE operator may use
one checkpoint family; never overlap training/evaluation. study operator.lock
guards the family; low-level APIs assume one operator. Resume by repeating the
bounded controller: complete checkpoints are skipped and exact cursors resumed.
Sources/game/chance must match. Native-double SQLite blobs require the recorded
x86_64/little-endian runtime; cross-endian migration is unverified.

Observed cache generation1508s with2CPU, initial full epoch about1168s during cache
generation, later full sweeps/evaluations roughly700–760s each. Main peak observed
629708KiB; task limits8GiB host,2CPU,2GiB board working-set guard,12GiB disk cap.
Checkpoint/cache are about3.2GiB before the additional warm trial. Remaining
iterations to0.1BB and release hours UNKNOWN; do not extrapolate a finish date.

The short CI verifies monolithic parity,atomic resume,guards,population/source
identities and research artifact qualification. It DOES NOT regenerate/replay
the full1755 numerical experiment. Those are explicitly local measurements.
No successful old workflow was manually rerun. No production/main/fees/SSO change.

# Preflop MVP acceptance: source comparison and shortest remaining path

This is a delivery plan, not a change to the owner's formal requirements.
No postflop UI or exact solving of every postflop state is required for the first
release. A justified continuation approximation and verified preflop outputs are
required. More postflop-only research/iterations cannot by itself finish the MVP.

## Sources inspected

- Owner task requirements: preflop RFI,vs-open fold/call/3bet,vs3bet fold/call/4bet,
  169 frequencies,verifiedEV,MTT/ring,2–9players,formal stacks,positions,BBante/rake,
  formal sizes,search UI. Facing4bet strongly prioritized.
- `docs/qa/ev-precision-20261030/ACCEPTANCE.md`: existing12-item release checklist;
  records0/12, approximation validation rather than mandatory exact postflop.
- `gto/README.md` and `docs/qa/gto-active-20261020/acceptance.md`: full scope explicitly
  retained; synthetic20equal-stack fixtures are not the original owner/G11 list.
- `docs/workers/GTO_NATIVE_TRAINING_BATCH_20261023.md`: original20stack source absent.
- `gto/abstract/model.py`: explicit researchHU50BB,blinds.5/1,noante/rake,
  raise-to2.5/9/21/50BB. These are not an authoritative complete sizing registry.
- `gto/abstract/study.py`: existing independent preflop abstract solver and169range
  exporter, with checkdown/fixed controller models and independent-seed evaluation.
- `src/GtoPreflop.tsx` and previous preflop UI evidence: existing search/range
  interface; eight opt-in research contexts/1352rows and HU1BB must stay protected.
- `docs/qa/reference-calibration-20261031/SOURCES.md`: exact-condition trusted169EV
  reference not acquired; free GTOBase candidate still has unverified full settings
  and export/reuse permission. No paid/auth-bypassed acquisition.

The12-item checklist is available; the original20stack/sizing list is **not**.
This reconciliation must not be reported as recovering that missing original.

|#|Owner requirement|Formal result|Concrete remaining deliverable|
|---|---|---|---|
|1|RFI|PARTIAL|Train/evaluate an independent full169 preflop profile with validated continuation/payoff uncertainty; root BR evidence|
|2|vs open F/C/3bet|PARTIAL|Same complete preflop tree, all169 action frequencies and actionEV intervals; legal sizing/config coverage|
|3|vs3bet F/C/4bet;vs4bet priority|PARTIAL|Same coherent game; all169 support and later action responses, not only local reached subgames|
|4|169-hand frequencies|PARTIAL|Export sum-normalized legal rows with policy/condition hashes and explicit missing coverage; current8research contexts are not formal data|
|5|VerifiedEV|PARTIAL|Bound sampling,missing-board contribution,local convergence and continuation abstraction separately; legitimate reference or independently justified approximation validation|
|6|MTT/ring|PARTIAL|Validated policies for both required formats; HU chipEV zero-rake research alone insufficient|
|7|2–9players|PARTIAL|Actual condition-specific ranges,not just EV/oracle regression tests; do not apply HUzero-sum exploitability certificate to multiplayer|
|8|Formal stack profiles|BLOCKED|Original20profile registry and expected semantics; never replace by synthetic20orHU50only|
|9|Positions|PARTIAL|Required table/position-specific strategy dataset; current new evidence onlyHU SB/BB|
|10|BBante/rake|PARTIAL|Policy datasets at authoritative conditions,not only existing settlement/oracle tests|
|11|Formal bet sizes|BLOCKED|Authoritative full sizing specification and legal tree coverage; explicit2.5/9/21/50is research only|
|12|Poker ID range search|PARTIAL|Admit only qualified verified range/EV artifacts through existing UI; keep research data labelled separately|

Formal PASS remains0/12. None of the above is waived by a small restricted
postflop NashConv, complete169row counts or CI success.

## Shortest implementation path to usable RFI + 3bet

1. **Condition registry in parallel with engine work.** Recover original stack/
   sizing/mode requirements and provenance. Block only dependent formal acceptance;
   continue explicitly configured HU50research. No invented formal presets.
2. **Connect full-support class-pair continuation values to an independent preflop
   research solve.** Reuse the existing preflop action tree/169exporter and the new
   readonly class-pair coefficient/oracle API. Do not edit the original frozen CFR.
   Scalar EV conditional on one reached range is insufficient for counterfactual
   actions. Never turn missing boards/leaves into0or extrapolate a point kernel
   from the selected high-reach sample.
3. **Fill/calibrate the payoff oracle rather than optimize4plans again.** Use
   full-support importance/stratified integration with card removal and explicit
   perclass/action uncertainty, or exact integration where affordable. The present
   selected-board kernel intentionally leaves wide intervals. Root BR requires
   off-reach class payoffs as well as on-policy means.
4. **Maintain one coherent game when learning.** Fixed postflop controllers define
   a valid preflop-only game but not full-poker equilibrium. If updating continuation
   policies with preflop ranges, preserve a fixed information abstraction and
   proper counterfactual reach; simply re-solving a different posterior game each
   iteration is not an established global CFR convergence proof. Validate the
   approximation against independent richer models/authorized matched references.
5. **Preflop qualification and UI admission.** Run independent registered conditions/
   seeds, report root BR/gain bounds and continuation sensitivity; export169F/C/R
   frequencies and actionEVs forRFI/vsopen/vs3bet(vs4bet priority). Production error
   thresholds need a traceable release definition; current0.1BB criterion is only
   a research subgame target. Do not silently promote it to a formal full-game
   acceptance threshold. Admit only evidence-qualified artifacts to existing search.
6. **Complete formal condition coverage with the same pipeline.** MTT/ring,2–9,
   positions,ante/rake,20stacks/sizes remain mandatory. This work is distinct from
   adding a public flop/turn/river product, which is future scope.

Immediate next engineering bottleneck after this batch: a sufficiently precise,
full-support class-pair continuation oracle and a new coherent preflop research
profile. Repeating successful CI or increasing only a few reached subgame
iterations is not the critical path. No owner approval for safe implementation is
requested; production deployment/main merge/fees remain forbidden.

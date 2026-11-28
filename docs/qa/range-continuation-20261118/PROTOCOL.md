# Range-conditioned continuation gate, fixed before outcomes
Source76d8a9cec17d1ef9cc6dadeb423b4f99dfafee5e, preserve old B/A/8candidates.
No UI/public feature/registry/prod change. HU50 ante/rake0 isolated only.

New public-range one-street CFR: replay exact public Betting history, factorized
private realization ranges with exact disjoint-card joint mass. Preflop B fixed.
Postflop all candidate holes use ONLY current board; actual other hole/future
cards never enter provider. Current5/6/7card rank buckets (8),32CFR iterations,
check/halfpot/jam andfold/call responses; deterministic public plans. Unknownlegal
sizes create a fresh exact-ledger subgame, no nearest-size translation.1%uniform
legal tremble defines positive postflop action likelihood; zero-reach preflop
histories use explicit uninformative off-path beliefs, not fold completion.
Flop/turn current-strength surrogate ignores future improvement: error UNKNOWN.
Card-removal is exact in joint bucket mass; private/bet abstraction errorUNKNOWN.

Compile/pilot <=60sec, native64world performance/legality gate <=30sec. Stop if
incomplete or state error; no time-dependent policyiterations. If feasible, known
riverjam gate: preflop remains B so old nut-event E supports every nonzero
BB rivernut-deviation payoff difference. Reuse baseline8192world count56events.
Fresh rejection sample256E-events (seed17118202, <=120sec), evaluate old/new paired
native BB-deviation gain only on E. E defined by old B (same preflop/cards), not
new outcomes. GainD=old-new supported onlyE, bounded[-100,149]BB. Conditional
Hoeffding lower plus exact-binomial P(E) lower, union99.9%, gives root reduction
lower. Requires positive reduction and no catastrophic new EV in pilot before
extension. No full BR/NC upper substitution.

Explore NEW river-allin bluff and flop-halfpot deviations separately (freshseed,
small fixed native batch <=60sec), not just oldnuts. If known gatefails stop.
All169/all-size work only if measured throughput permits <=90sec; else report
UNKNOWN/incomplete and preserve receipts, no long no-progress computation.
Local study compute cap300sec/disk100MiB, checkpoints/frozen config/digest saved.
Quality/formal12 gates unchanged; no normal registry while incomplete/refuted.

Pre-conditional refinement: add16bucket variant (same32iterations) to8bucket
candidate. Pilot64worlds/config <=30sec; choose neither based on hidden cards.
Evaluate BOTH on SAME256fresh E-events; confidence split3ways (eventmass lower,
D8conditional lower,D16conditional lower), total99.9%. D support[-100,149].
Only a candidate with positive ROOT reduction lower may get new-deviation probes.
Source E count56/8192 is reused from fixed previousreceipt, not reestimated by
optional stopping. Conditional sampling stops after256Eevents, not after a desired
payoff; rejected-world count is not used as an eventprobability estimate.

Both known-reduction gates passed; extend ONLY default/faster8bucket frozen digest.
Fresh256worlds seed17118203 <=60sec: baselineold/new + new-policy BB riveralwaysjam,
BB flophalfpot, SBroot3.5BBopen, BB10.5BB3bet deviations.5paired contrast intervals
(new-old EV +4legal deviations), family99.9%. No claim of completeBR upper from
these probes. Then if no positive independent BR lower, fixed2048world EV study,
seed17118204 <=120sec, checkpoint64worlds/RNG,3EB intervals(newEV,oldEV,diff).
Followup cumulative compute still<=300sec; no further training.
All-action129792rollouts cost estimate frommeasuredthroughput exceeds90sec, so
full169/action precision must remain UNKNOWN for this newdigest. If budget permits,
produce explicitly PARTIAL169x2canonical-action EV samples (no formalPASS), and
scan exact legal raise-to responses. Do not reinterpret partials as formal12PASS.

Validation-found defect: new public-history replay did not decode native -3 marker
(normalized raise-to-one shortallin action3). Minimalgeneral decoderfix+native
regression; no old solver changed. Finaldigest conditional cohort replayed natively,
all numerical gains identical, previous incompletecontroller hashes preserved.
Failed probe seed17118203 used only fordebugging; NEW quality probes seed17118205.

Known-probe scope check before new outcomes: originalguardlive1/3/10BB can stop
triggering after strategic bets changepots. GeneralizeBBnutsjam to ALLmatched
riverpots; forpassiveoldB this is identicallyoriginaleventE, so old56/8192mass
receipt stillapplies. New generalizedgains also0outsideE because preflopunchanged.
Fresh seed17118206,512conditionalEevents, default8only, <=120sec, two-event
confidencefamily99.9% (mass lower+conditional reduction lower). Never use rejected
attemptcount as eventprobestimate. This is an additional robustness gate, not an
unreported change to originalprobe. Extend overall localcompute cap to420sec
BEFORE generalizedoutcomes, after known reduction gatepassed; no new training.
Use only a passing generalizedcandidate for further eval/probes.

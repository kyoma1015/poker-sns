# Multiway preflop batch

Input public HEADab074aac0636daf3eac36f21d5349592c05b9db8, CI40355014847
SUCCESS526cases. Localc098c2a has identical treec45bc684664dc6ab13b921aa1043e828a934b202.
Existing four commits retained; initial working tree clean. Scope GTO only.

Acceptance criteria recorded before implementation:
1. Seat-labelled ordered opponent hole-card assignments for2..9players, exact
   card removal, normalized explicit joint priors, no duplicate ordered deals.
2. Independent-range product enumeration must be bounded and fail without
   silently dropping candidates. Product priors must remain distinct from a
   learned observation-conditioned posterior or recovered full-game range.
3. Reuse real NativeState public-history replay and exact per-player/chance
   factors; posterior, evidence and hero-excluded reach calculated separately.
4. Check information-set policy consistency for every queried actor, not hero
   alone. Frozen native snapshots must reject unknown rows.
5. Multiway EV vectors conserve chips plus rake; sampled intervals control only
   sampling error. Calls continue through native postflop, never fake showdown.
6. Preserve existing tests and three native variants. CI on actual public head.

Full release acceptance remains unfinished: genuine complete learned support,
formal20stacks/sizes, representative poker convergence, verified169EV and app UI.
No production/main/billing operations permitted. No independent restart exists.

Implementation recovered and ready for publication2026-10-27:
- joint_support.py: ordered seat-labelled joint priors; hero/other-seat/public
  blockers; exact retained/removed mass; bounded independent-range products.
- joint_reach.py: actual NativeState history factors and posterior; all-actor
  queried infoset consistency; arbitrary hero seat; multiway sampled policy EV
  and common-prefix interventions with sampling-only confidence intervals.
- Prior executor native runs:16methods per Next/Cache/Packed=48PASS. Logs retained
  in docs/qa/multiway-20261026. A fresh runtime lost temporary native modules;
  local reconstruction/network approval did not complete. Do not describe those
  old logs as a fresh native rebuild. The PR CI will rebuild all3 with existing
  pinned versions/archive hashes and rerun the entire suite on actual publicHEAD.
- Fresh dependency-free suite:24PASS (previous18+6joint-support boundaries).
  CI target580=previous526+6pure+48native executions, pending actual CI evidence.
- Genuine reach assertion is conditional: probabilities are exact under supplied
  joint priors and actual queried policies. A regression uses a frozen actual
  learned native row. Full-game learned prior coverage/convergence remains
  unproved; supplied independent seat ranges are explicitly not learned ranges.
- Side-pot/rake EV is checked against native finite exact oracle and hand-derived
  three-way10/6/2-chip settlement; shared native settlement is not an independent
  proof of every poker outcome. No fake showdown approximation introduced.

User clarified formal20stacks/sizing source location is unknown. Continue source
search without guessing; block only dependent acceptance, not independent work.
Next: bind multiway output to immutable policy/configuration; connect learning
observations and honest convergence diagnostics, then verified-only range UI.
No autonomous restart configured; no production/main/billing operations.

## First public exact-head verification
Published6888cd5ee41d3ee407bd80b8b810259ba2063aef, same treeac9f96c36b81be883592d7c9fac54eb2cafb9fad
as local635e70f. CI40452009763/job122016675924 SUCCESS. Decoded log proves555
unittest executions+25Packed cases=580PASS (previous526,+54), all3pinned
native reconstructions PASS. Temporary local environment remains missing; CI is
the fresh reconstruction evidence. Existing four historical commits retained.

## Learning/evaluation continuation
New learned_preflop.py freezes actual native policy at checkpoint iterations,
queries finite joint-support preflop contexts and saves fresh checksummed
checkpoints plus exact-rational JSON reports. Config/policy/input digests bind
results. Typed missing-row errors preserve computed actions and mark unknown
prefixes/continuations unavailable; failed attempts still reserve sample budget.
Target frequency rows remain unknown when unobserved, never uniform guesses.

New local deviation diagnostic reports unilateral improvement for the queried
decision/belief only, with conservative intervals. Missing positive-mass profile
actions prevent estimating the profile value. Omitted legal alternatives prevent
a full local upper bound. Global exploitability/NashConv remain null; no division
by2 or two-player zero-sum convergence claim is applied to multiplayer games.
Policy total variation across training checkpoints is observational drift, not
a convergence certificate. Formal verified-convergence condition count stays0.

CLI (queries contain exact string priors, e.g."1/2"):
python3 -B -m gto.native.learned_preflop --module-dir BUILD/g12_next --stacks 100 100 --seed 17 --checkpoints 200 400 --queries queries.json --output FRESH_OUTPUT
Use --seed 17 (separate arguments); examples use legal illustrative sizes, not
the missing formal size specification. Query histories []/[8,20]/[8,20,44] map
to RFI/vs3bet/vs4bet with suitable hero seats0/0/1, BB2. These are scheduled
contexts, not claims that the learned policy covers or solves those contexts.

Fresh pure regression30PASS (+6). New actual-native integration8methods per
variant is pending CI: expected610=580+6pure+24native. New cross-variant proof
compares full400-iteration learned snapshot digest and deterministic three-way
fold/call/re-raise report bytes. Native integration is not locally rerun because
the temporary compiled modules disappeared and approval-gated local dependency
reconstruction did not complete. All failures must be resolved in exact-head CI.

Release acceptance is intentionally not counted from test totals: RFI/3bet/4bet
verified-GTO settings0, full verified equilibrium169EV coverage0/169, UI not
connected. Multiway explicit-support conditional engine now2..9 seats; complete
learned joint support remains unproved. Missing formal configurations block only
formal-spec acceptance. No other development-line source files were changed.

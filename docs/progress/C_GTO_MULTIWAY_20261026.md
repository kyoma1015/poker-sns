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

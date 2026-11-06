# Independent coherent preflop path, not a real-game GTO certificate

Explicit HU50BB,no ante/rake,SB/BB0.5/1,raise-to2.5/9/21/50BB. Two fixed
learned own/public flop controllers define two different coherent preflop games.
All nine matched terminals have169²counterfactual payoff support,including off-
reach classes. Original frozen CFR and eight older research ranges are unchanged.
Teacher development32boards/8textures; pilot16,training256,evaluation512 independent
IID physical-board draws. Each flop integrates all compatible concrete private
pairs and990turn/river runouts. Fullsupport estimator is NOT fullboard enumeration.

`protocol.json` and `design.json` were committed before fitting. `teacher.json`
fixes postflop profiles. New preflop policies are frozen before evaluation; no
final model selection. `results.json` stores every exported row, intervals,
convergence trace, model scope and source identities. To avoid committing30MB of
base64 arrays, six numeric packets retain exact binary SHA256/count fingerprints;
`independent_verify` validates regenerated payloads before checking these exact
fingerprints. Full local arrays are preserved in
`/workspace/independent-recovery-20261106/full-results.json`; cache
`/workspace/independent-oracle-cache` has all raw computed contributions.
No numeric array is silently replaced by0. CI rebuilds actual arrays from seeds.
Cross-platform bit identity is checked strictly for these fingerprints, whereas
ordinary decoded values use1e-12; a mismatch fails rather than being hidden.

Actual training-table NashConv small0.001509176,large0.001423194BB. Expected-game
independent intervals small[0,7.711587009],large[0,11.665099038]BB:0.1research target
FAIL. Simultaneous percell interval families each99.5%,both99%; whole-policy
correlated observations have a separate99.5%family (eight rows),all families98.5%.
Whole-policy EV small0.028773864[-0.653145989,0.710693718],large0.035898531
[-1.186627370,1.258424433]BB. Candidate gains include0. External comparison NOT
PERFORMED; real-game approximation error UNKNOWN. Size sensitivity is not accuracy.

Research UI adds8contexts/1352rows behind explicit opt-in and exact conditions.
Normal verified catalog remains unchanged; no ordinary-GTO admission. All twelve
formal requirements remain:0/12. Original20stack/fullsize source unresolved. Old
8ranges1352,H U1BB,2–9regressions,staticdemo and frozen core remain protected.
Local13Python/20Node tests and build passed. Mobile was blocked by environment
EPERM,not a PASS; new CI must verify it. No production/main/SSO/fee changes.

Rebuild with independent_preflop phases design/teacher/train/export, fresh output
paths, pinned protocol/source. See the GTO reached-range workflow for exact
commands. Recovery first: gitstatus,verify local/public ancestry,keep uncommitted
files and /workspace/poker-sns objects. Never reset --hard/clean/forcepush.

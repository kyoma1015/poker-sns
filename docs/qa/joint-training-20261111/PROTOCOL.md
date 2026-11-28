# Switchable training kernel: preregistered engineering and quality gates

Parent is the actual completed CFR+epoch3 DB, not invented frozen-policy regrets.
Keep original modules, all original checkpoints and cache bytes unchanged. New
lossless compressed overlays refer to a quiescent read-only parent with numeric
digest; backend/source/parent/game identity pins checkpoint resumption. Legacy
and vector can be selected for separate new trials, never silently mid-resume.

Before population work: explicit two-board hidden-card tests compare complete
regret,ownreach average mass, current/average policies, exact independent BR,
counterfactual reach under zero ownreach, atomic rollback and deterministic resume.
Numerical arrays tolerance1e-8 BB, policies1e-8; exact parent/fork logical hashes;
same-backend restart bit-exact. Cross-backend hashes may differ due roundoff;
do not label floating-point tolerance as identical hashes.

Training performance experiment: same genuine epoch3 parent, all1755 orbits,
22100 physicalflops, same two owner sweeps/one additional epoch4. Separate legacy
and vector overlays, fixed order legacy then vector, one finite worker, existing
cache only, compilation excluded/reported separately. Each backend at most3510
training blocks,1800 activewall seconds, then independent original world-BR at
most1755 blocks/900wall seconds. Budget stops retain actual cursor/checkpoint;
do not extrapolate partial throughput as whole-training speedup. Record process
CPU,wall,peakRSS including Python/cache/compression/SQLite, logical numeric hashes,
array/policy max differences, raw training CPU ratio only if both epochs complete.
New compressed overlay uses2GiB filesystem free and3GiB overlay directory guard,
explicitly different from original uncompressed learner's4GiB reserve. This is
fixed before measurement; original learner's guard is unchanged. Abort
safely rather than deleting original files or changing the registered guard. Never adopt based
on throughput alone. All exact evaluation is limited-game, not realNLHE accuracy.

Quality gate before further population studies: new tiny teacher128-history
comparison, two games, same128 additional iterations. Candidates fixed now:
alternating full-history; delayed output averaging from newiteration33 while
retaining historical mass in the checkpoint; damping0.5; fixed25% realization
mixture with teacher. Report final and best checkpoint at32,64,128, pureBR same
game; candidate selection uses optimization game,not independent test. A candidate
may be registered for later population work only if final NC improves teacher
and full-history alternating in BOTH games by at least10%, with no worst-game
regression. No candidate expansion after results. No new full quality trial is
authorized by this protocol alone; a separate source-pinned budget must precede it.

Immutable frozenNC0.9321071527220774BB remains adoption baseline,0.1BB research
target unchanged. Formal0/12,ordinaryGTO0,UI0 unless new independent evidence.

# Pre-outcome identifiability amendment

Registered after the original workers began, BEFORE any candidate epoch1 BR
result was completed/read. This is disclosed, not silently rewritten prereg.
Original registration.json and2epoch logs remain unchanged.

Independent algebra: R0=epsilon*pi and S0=0. At the first update clipping negative
regrets does not change RM's positive part. DCFR t1 discounts both signs by1/2.
Therefore all three methods use the same behavioral strategies in iterations1/2
(up to roundoff), and vanilla-linear versus CFR+ averaged policy after2iterations
is identical. Two epochs compare averaging only, not the regret schedules.

To identify the update schedules, retain actual independent checkpoints1/2 and
add exactly epoch3 for EACH of the same three candidates. No candidate selection,
no changes to game, initial policy,0.1BB target, or the original7200s per-method /
10800s operator time cap. If remaining ORIGINAL time is insufficient, leave3
incomplete/UNKNOWN; do not extend budget based on results. No new data service.
The already-running two-epoch workers are not restarted or source-migrated.
A separate finite controller resumes the SAME method-identity SQLite once the
original worker completes, for one additional epoch/evaluation. Do not edit the
joint_updates.py/.cc sources while those checkpoints are active.

This amendment follows structural audit evidence, not an observed HU50 quality
failure. Store the UTC timestamp and hashes BEFORE the first epoch1 BR result.

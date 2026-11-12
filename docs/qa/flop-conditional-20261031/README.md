# Actual fixed-flop conditional measurements

HU50BB, rake/ante0; actual frozen flop_controller preflop policy unchanged.
Flops fixed BEFORE measurement: Ac7d2s (48,21,3), Ts9s8s (35,31,27).
Hero CALL and whole preflop history conditioned BEFORE this public flop.
Exact posterior over compatible hole assignments; not uniform169 classes.
169 strata,32 draws WITH replacement per stratum; all990 turn/river runouts
per draw enumerated exactly. Win/tie/equity are separate fields.

| stage | flop IDs | old BB | new BB | delta BB | simultaneous sampling interval |
|---|---|---:|---:|---:|---|
| vs_3bet | [48, 21, 3] | -3.778475109 | -11.223102538 | -7.444627428 | [-24.511565708639637, 9.622310852222235] |
| vs_3bet | [35, 31, 27] | 0.337426792 | 0.094497452 | -0.242929340 | [-16.97485046417767, 16.488991784840486] |
| vs_4bet | [48, 21, 3] | -5.607873546 | -7.504159664 | -1.896286119 | [-27.765235419700918, 23.972663182593248] |
| vs_4bet | [35, 31, 27] | -1.273481813 | 0.423751145 | 1.697232958 | [-25.16658526851547, 28.5610511849272] |

Old: original saved fixed card controller applied to this actual flop, not
its unconditional averaged kernel. New: fixed experimental raise/call with
legal effective-stack cap, NOT learned. Net BB before posting blinds.
This is DIRECT CALL continuation only. Do NOT subtract the previous whole
facing-node / unconditional-board table and call it model improvement.
All4reports and class/aggregate intervals jointly>=99% under stratified
independent pseudo-random hole draws. No turn/river Monte Carlo error.
Wide hole-sampling intervals do not establish sign or GTO accuracy.
Model approximation error UNKNOWN; external GTO deviation UNKNOWN.
No reference fit, strategy update, new release/UI range or formal acceptance.

ContinuationProvider receives own holes, public flop, actor, pot and stack.
It cannot directly access opponent holes or future board. This is a training
integration interface, NOT an implemented continuation learning algorithm.

Reproduce:
python -B -m gto.abstract.flop_conditional --build-dir /tmp/flop-native --output /tmp/flop.json --samples 32
Compare with gto.abstract.verify_export at unchanged1e-12 and identity hashes.
Original frozen-input archive validates its policy/kernel hashes on load.
New output also binds condition, policy digest, input hash and method sources.

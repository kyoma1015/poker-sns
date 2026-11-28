# Registered update audit and finite population comparison

Base508a91b36ed00c6e17dee150122311125a77a486. Previous frozen NC0.932107152722,
warm vanilla2 NC1.190819543932 and uniform4 NC3.081906371316 are already observed.
This is optimization, not unseen-board or external validation. Preserve all.

Before training: independently enumerate a small hidden-card/public-chance game,
all deterministic BR policies, and hand-derived counterfactual gradients/own-reach
average weights. Include asymmetric correlated chance/card removal, zero-own-reach,
zero-opponent-reach, shared preflop info across future boards, SB/BB zero-sum signs,
normalization. Audit regret matching and update schedules on analytic matrix games.
Training-only kernel must match the unchanged original gradient/average outputs;
independent evaluation always uses the original full BR kernel.

Population comparison: identical full1755/22100/9branch HU50 game/cache; frozen
small behavioral prior R0=1e-15*pi, S0=0 for every candidate. No frozen file edits.
Existing completed vanilla uniform-average2 is the witnessed control, not rerun.
New candidates (ALL outcomes retained): vanilla with linear averaging t; CFR+
R=max(0,R+g), linear averaging t, simultaneous updates; DCFR(1.5,0,2) with
R_t=(R_previous+g_t)*[t^alpha/(t^alpha+1) if positive else t^beta/(t^beta+1)],
S_t=(S_previous+ownreach*pi_t)*(t/(t+1))^2. No alternating-CFR+ claim.

Each candidate gets exactly2 full epochs. Checkpoints0/1/2 retained. Epoch1 is
independently evaluated if budget permits; otherwise prove realization-equivalence
to the frozen profile over every board and label reused baseline BR as derived,
not newly measured. Final2 evaluation must be actual complete independent BR.
No post-result candidate budget extension, no changing target0.1BB, no ordinary
GTO admission. Report every candidate and SB/BB gains versus frozen/control.

Budget: two CPU cores maximum, each finite worker7200s, total operator wall10800s,
RAM2GiB/worker and cgroup8GiB, new trial data cap8GiB and filesystem free guard4GiB.
Existing~9GiB caches/checkpoints/backups retained unchanged. No dependencies,
network data purchases, cloud services or paid changes. Atomic state+cursor,
method/source/game identity, interrupted resume equivalence mandatory.

Model omissions/private abstraction/external comparison UNKNOWN remain unchanged.
Official12 acceptance0/12, normal0. Original20stacks/fullsizes remain missing;
researchHU50 sizing is not a replacement. Preserve originalUI/frozenCFR/demo.

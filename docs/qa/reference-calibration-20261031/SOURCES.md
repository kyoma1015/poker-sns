# External reference qualification — 2026-10-31

Target: NLHE HU,50BB before blinds,SB/BB0.5/1,no ante,no rake,chipEV,
raise-to2.5/9/21/50BB,limp and the complete pinned preflop tree. A numeric
match in stack depth does not establish an equivalent game. Required: legitimate
169-hand/action frequencies and net-EV data, tree/continuation settings, solver
version, convergence evidence and usage permission. No subscriptions purchased,
trials activated, account/auth restrictions bypassed or providers contacted.

| Candidate | Primary source | Observed reason not usable as an exact numerical reference |
|---|---|---|
| GTO Wizard HU drills | https://blog.gtowizard.com/how-to-improve-your-heads-up-game/ | The documented no-rake drill set covers30BB and below; not HU50BB |
| GTO Wizard custom preflop | https://help.gtowizard.com/how-to-build-custom-solutions/ | Custom stacks/rake/tree supported; HU custom solving requires Elite beyond the free<=10BB test. No existing entitled50BB export acquired; new paid access prohibited |
| GTO Wizard MTT HU library | https://blog.gtowizard.com/status-and-info-about-our-solutions/ | Provider's historical listing includes50BB but with0.125BB ante; not no-ante. This2021 listing is not proof of current full catalog availability |
| MonkerGuy HU cash50BB | https://www.monkerguy.com/ | Listed4% rake/0.3BB cap;50BB open2x/2.5x and3bet3.5x. Rake and tree differ; paid export not acquired |
| MonkerGuy HU SNG50BB | https://www.monkerguy.com/ | No-ante pack includes50BB, but detailed sizing, rake/utility and convergence metadata not established from public listing; paid export not acquired |
| HRC free HU Nash | https://www.holdemresources.net/hune | Explicit push/fold game, not the raise/call/3bet/4bet tree. Tables omit detailed mixes and do not provide HU50BB action EVs |
| ART/GTO free preflop | https://artgto.com/gto-solutions/ | Published library is100BB6-max; heads-up pots after folds are not an original2-player50BB game |
| GTOBase HU Cash | https://gtobase.com/ and public get_libraries_no_auth metadata | Provider documents no-rake chipEV and free HU50–100BB. Public catalog confirms50/75/100BB,spot107. Public app needs JavaScript; exact tree/ante/169hand EV export not acquired; exact match UNKNOWN |
| Preflop Guru HU | https://preflopguru.com/login/ | Public module catalog includes50BB no-ante; full sizes/rake and exported169hand EV unavailable in inspected public metadata; paid plan not activated |
| GTO Wizard open-shove illustration | https://blog.gtowizard.com/introducing-quantal-response-equilibrium-the-next-evolution-of-gto/ | Same HU50 no-rake/no-ante physical description, but illustrative open-shove/QRE line and unspecified wider tree, not the pinned2.5/9/21/50BB tree or complete169hand dataset |
| Independent Python preflop solver | https://github.com/chirenonhive/poker-solver | Author identifies deep-stack100% equity-realization approximation; no independent real-game precision proof. Another approximation is not a trusted exact reference |

HRC documents the distinction between preflop abstraction and dedicated board
solves: https://www.holdemresources.net/docs/postflop/ . That is methodology,
not an acquired matching reference dataset.

Outcome: trusted condition-matched169-hand datasets acquired0. External frequency
comparisons0/676 and EV comparisons0/676 PER MODEL. Numeric differences UNKNOWN,
notzero. Absence from these inspected sources is not a claim that no such solution
exists anywhere. Two current models remain research-only; their relative model
sensitivity is not external accuracy calibration.

Public GTOBase catalog was retrieved without authentication using the public frontend's documented-in-code get_libraries_no_auth call. HU Cash spot107 is_free=true and lists50/75/100BB. Its ante, full tree, EV basis and export/reuse permission are not established by that catalog. Public HTML/JS were readable; browser execution hit an environment startup error. No protected strategy endpoint was queried, no account created and no private credentials used. Thus this promising free candidate remains OPEN rather than being rejected as paid or mismatched. Provider example QRE output is not automatically treated as Nash reference.

## Reproducible comparison

`python -B -m gto.abstract.reference_compare --reference <authorized-normalized.json> --mode flop_controller --output /tmp/comparison.json`

Input schema `pokerid-external-preflop-reference-v1`: traceable source URL,solver,
retrieval date,usage permission; explicit target-condition fields (see
`target_condition()`),net_bb_before_blinds EV basis,and four contexts. Each context
must state actor,exact history,labelled actions,hand-class frequencies; optional
EV/reach fields remain missing rather than zero. No automatic export scraping or
cost-basis guessing. Source evidence must be independently checked; a self-declared
matching schema never grants trust or publication permission.

Comparator reports per-hand frequency differences/TV,combo-weighted and reference-
reach-weighted TV,descriptive EV distances,coverage and condition mismatches.
Action order may be permuted,not padded or interpolated. Different trees/actors/
histories are not compared. Different physical conditions are REFERENCE_ONLY.
A deterministic hand/history partition is declared before any reference fitting;
its audit holdout is not for tuning and is not an independent-sample statistical
confidence interval. No reference data has been used to fit either model.

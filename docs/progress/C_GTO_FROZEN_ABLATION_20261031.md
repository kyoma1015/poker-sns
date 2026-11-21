# Real frozen-policy ablation measurement
Acceptance BEFORE implementation: public6580ff1840f6d9967f15a56e242b62acce1ca4d3
imported without content changes (tree77488783e7ca5d5928c154de0837ca4cc779882e).
Original local b729aa5 was clean;9upstream added files preserved. Local history is
a metadata shadow; publish only new fixes parented to public6580ff1,verify tree.
Existing19 ablation tests PASSED; no failing original case was fabricated.
Raw workflow endpoint finds actual push CI41183100044 SUCCESS. Specialized
fetch_commit_workflow_runs filters to pull_request and omitted this run; workflow
was not actually absent. Never rerun that successful job to fix a display issue.

Audit: enforce normalized decision rows/chance; explicit BB/OOP seat and kernel
orientation; call-conditioned frozen reach; derive real post-call pot18/42BB and
remaining stack41/29BB; cap legal flop contributions. EV basis and sampled public
board averaging must be explicit. No inference of learned flop policy from
preflop policy. Deterministic experimental bet/call and raise/call are model
parameters,not played/learned strategies. Primary measurement also evaluates the
existing saved card-dependent flop-controller kernel versus checkdown.

Load committed SHA-verified frozen-input packet: seed1701 two fixed policies,
heldout seed700017,S256,exact blocker probability from1624350 ordered deals.
Report conditional-on-call net BB values plus actual before-call reach when
requested; separate sampling CI,model approximation UNKNOWN,external GTO UNKNOWN.
Reproduce report in existing working precision workflow (using its rebuilt
refined kernel) and register new tests; no browser/production/UI publication.
No synthetic unit fixture numbers may be reported as real-data measurements.
Formal0/12 unchanged,old data/controllers/8research/HU1BB/2..9 preserved.

## Implemented
Original19tests remainPASS. Added10 meaningful regressions: corrected BB/OOP
ordering,normalized decisions/chance,call-conditioned reach,pot/remaining-stack,
all-in cap,forbidden raises,paired-world uncertainty,real archive invariance,and
full decision-node values independently checked against existing C++ CF evaluator.
Full29tests PASS locally. Synthetic legacy replay is explicitly separate from
real measurements; baselineBB/OOP fixture was wrong and correction is verified.

Existing source had no runner failure: push workflow41183100044 wasSUCCESS,
but the specialized connector list filtered outpush. Use raw actions/runs filtered
byhead_sha to include bothpush andpull_request. No successful CI manually rerun.
Existing working precision workflow now also runs29tests and regenerates the
actual measurement from its rebuilt kernel; targetedpush workflow includes new
regressions too. This is new-code CI,not a manual repeat of oldsuccessfulCI.

Input source: committed frozen-inputs packet(two actual full policies,seed1701)
and saved refined rb-kernel-demo(seed700017,S256),exactly the previous verified
kernel design. ExistingCFR/kernel sources/policies/browserdata/HU1BB unchanged.
Complete facing-node calculations include all frozen current actions and all
later preflop responses. DirectCALL tables are separately labelled. No synthetic
strategy/equity fixtures are used for the measurement output.

Flop-controller-trained frozen preflop policy,full facing-node netBB:
vs3bet old savedcard=-1.2936149717,new raise/call=-2.7987355070,
delta=-1.5051205353,simultaneous sampling interval[-1.6562107227,-1.3540303479].
vs4bet old savedcard=-5.0424264692,new raise/call=-5.4447262684,
delta=-.4022997992,interval[-.6562768030,-.1483227953].
These pure experimental flop protocols are NOT learned flop strategies and
use class-conditional public-board-averaged showdown equity,NOT fixed-flop
equity. The deltas are model sensitivity,not GTO exploitability or field profit.
No improvement is accepted. Model approximation/external GTO deviation UNKNOWN.
Same frozen policy,private-card removal andnet-before-blinds basis in each row.
All72reported intervals jointly>=99%; paired seats/planes are grouped,known exact
cells excluded from sample uncertainty. Both originalpreflop models are reported.
Formal0/12 and ordinaryGTO release0 unchanged.

## Resume
Check latestHEAD/dirty state/raw ALL-event CI list. Read
 docs/qa/frozen-ablation-20261031/README.md andrefined-results.json.
Run python -B -m unittest tests.test_flop_tree_ablation tests.test_flop_reach_adapter
 tests.test_frozen_flop_reach tests.test_frozen_flop_ablation
 tests.test_frozen_ablation_study -v.
Reproduce real report with python -B -m gto.abstract.frozen_ablation_study
 --kernel <rebuilt precision-study/rb-kernel.json.gz> --output /tmp/measured.json.
Existing workflow verifies golden numbers+source/input hashes within1e-12.
Next: genuine board-conditioned flop equity and an independently trained/heldout
continuation policy,legal action tree,external matched reference. Do not call the
pure experimental protocols an optimized poker strategy. No production/main/
Storage/SSO/otherPR/fees changes;AUTO-RESUME/independent restart absent.

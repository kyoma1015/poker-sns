# Fixed-flop implementation acceptance
Base public5df7aa09d6e024c9e5d60a42d073ce2b75b35e48, clean shadow3690104.
Scope only new conditional evaluator/tests/CI. Existing frozen strategies and
research demo unchanged; no previous successful CI rerun.
Acceptance for measurement: exact990 against independent original rank; legal
public/private blocker counts C(49,2)*C(47,2); exact nonuniform history posterior;
seed determinism; normalized169class mass; no hidden opponent input to provider;
explicit stratified hole sampling vs exact runouts, bounded simultaneous intervals.
Two flops selected before measurement: cardIDs48/21/3 and35/31/27. Both stages,
one actual frozen flop_controller preflop policy. DirectCALL only,not whole-node
EV; no comparison with previous unconditional-node table as if same denominator.
Old saved card predicates are applied to THIS flop; new fixedraise/call is NOT
learned. Approximation/external accuracy remainUNKNOWN. Formal0/12.

## Local results
8new tests PASS. Initial independent-oracle loader mistakenly used build() path
as a loaded library; corrected to load(build()), then all8PASS. No native/source
or old data/controller changes were needed. Both2flops*2stages report169/169
reachable classes (676 rows),32draws/class=21632draws,21047unique concrete pairs
with all990turn/river enumerated per unique pair. Total20836530unique-runout
settlements. Repeated hole draws reuse exact counts, not independent runouts.
Posterior/sampling scope is directCALL,not whole facing node. Statistical bounds
wide; no sign certification or GTO improvement. Formal0/12,old8ranges unchanged.
CI: new narrowly scoped push workflow runs8tests and reconstructs output/hash
identity at1e-12. Existing successful jobs never manually rerun.
## Resume
Read actual publicHEAD/dirty state. Check raw actions/runs for push AND PR events.
New test: python -B -m unittest tests.test_flop_conditional -v
New measure: python -B -m gto.abstract.flop_conditional --build-dir /tmp/flop-native
 --output /tmp/flop.json --samples 32
Next: selective exact hole-pair integration or variance reduction, independent
seed validation, then learn ContinuationProvider using own Observation only,
keep training/heldout seeds separate. Full-game approximation/external reference
remainUNKNOWN. No owner decision needed; no production/main/Storage/fees changes.
AUTO-RESUME and independent restart absent.

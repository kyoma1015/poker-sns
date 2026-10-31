# Native initial-deal chance reach — interrupted work resumed 2026-10-24

Base PR120 aa5f94745ece3997b2324329018f73da95a4a062. Existing test input
cca4c0ed8dd9bacfe835fdbcab82354e2a5dc1c4 and uncommitted source were retained.
Before implementation the module was absent: one importERROR, zero executed
methods. Earlier Next-only pass log is preserved but not used to claim all three
variants had completed before interruption.

## Exact scope
For a full uniform 52-card ordered private deal to n=2..9 players, any particular
ordered own hand has P(50,2n-2)/P(52,2n)=1/2652. The two hole orderings of a
concrete hand combine to1/1326. This marginal depends on the initial chance model,
not on sampled visits, average-policy counts, or inferred uniform strategies.

The new API requires canonical NativeGame, no fixture or root-action conditioning,
empty board/history and the exact first native preflop actor/config/action set.
It inspects the actual native representative deal (52,51,... uniform outcomes)
and records exact rational probability plus native module/config SHA256.
Uniformity for all deals relies on the preserved State::chances/apply source
contract, not a claim that the single representative deal enumerates all deals.
The original native module/source provenance still needs the pinned build gate.
It cannot independently authenticate a deliberately forged solver's hidden C++
configuration; caller ownership and correct construction remain prerequisites.

Other seats/histories, runtime/public-config drift, fixture/root prefixes and
action mismatch are refused. No absent hand policy is invented. 1326 concrete
coverage and2652 ordered coverage are separate. Aggregation uses binary64-rounded
1/2652 but the evidence retains the exact Fraction numerator/denominator. EV stays
null, general strategy/counterfactual reach and full-poker convergence stay UNKNOWN.
This is a justified initial-chance marginal, not a full strategy reach estimator.

## Resume verification
First resumed command chose an old local reconstructed module directory lacking
pokerid_rules.py: all three runs failed with environment import errors. Those logs
are retained. No source/test change or repeated same-path failure was used to
hide it. The complete existing gto-native-final-20261020 modules contain the
hash-verified rules456225cf675a1b8ecf9ac7b16b7e3b6185900fe3dea75fe8f1687ad12354ea5a.
With these modules, unchanged10methods run separately on Next/Cache/Packed:
30PASS/0FAIL. Existing Python18 and exact reused hand169 acceptance33PASS.
Tests include2..9 players,20k-iteration full1326/169 coverage, expected pair/suited/
offsuit reach, exact400 vs200+200 checkpoint resume/RNG/policy/provenance equality,
and seat/history/config/action/fixture rejection. This is reconstructed native
behavior, not original G9/G11 ABI or historical checkpoint proof.

CI reconstructs all3 modules from pinned sources and executes the same new30cases
plus the previous157 cases (187 expected executions) and existing960 synthetic
smoke cases. npm build/lint are not applicable to Python-only changes. No old
source, C++/rules bytes, checkpoint, retained state, job, lease, reservation, main,
controller, production, paid service or autonomous startup is changed.

Next: action-history reach requires justified behavioral policy/conditioning;
EV requires a separate justified estimator. Keep the formal20stack/allbet/2..9/
MTT/rake/BBante/169freq/EV final specification unchanged. Original G9/G11 inputs,
historical compatibility and actual poker convergence remain BLOCKED/UNKNOWN.

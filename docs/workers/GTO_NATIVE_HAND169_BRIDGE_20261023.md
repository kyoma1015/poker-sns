# Native policy → 169-hand bridge and exact small-poker oracle

Base: PR115 13c4e7d3ea9250ecfb63044ae3711b0d12a91eae, not main.
Original G9/G11 and convergence gates remain unchanged. No original C++ artifact,
historical checkpoint or retained SQLite is changed.

## Evidence of format and exact reuse
Preserved `handoff/gto/g12_next/g11_native_state.h:23` State::info emits JSON with
betting_history, board, hand, public_config and seat. Hand is two integer card IDs;
`g11_rules_embed.h` five() uses rank=card/4+2 and suit=card%4. The bridge explicitly
labels suit IDs0..3 as c/d/h/s for export; this is a declared naming convention,
not a recovered original G11 naming claim. Suited/offsuit classification depends
only on suit equality. No guessed hidden fields or substring/card-name parsing.

The latest reviewed `gto/hand169.py` is reused exactly from PR103 commit
24ccde5490225d52b9e8328d86fa425bca59a664, git blob
e1757b99ff0d8c8072cc080c5427e42aa1107a33. Seven original PR103 acceptance files
are copied byte-for-byte in the same paths and run (33 tests); the original
hand169 unit test file already has the same PR103 blob. This is dependency reuse,
not seven new bug fixes. `reuse-proof.json` records every byte/hash comparison.
An initially unavailable local commit object caused a private intermediate empty
dependency file; full-SHA fetch restored the exact reviewed source before testing
or publication. No other branch/artifact was modified, and the history is retained.

## New bridge behavior
`export_context(solver, context, reach_weights)` uses one explicit preflop
seat/history/public-config context and identical action IDs/order. It refuses
missing, surplus or invalid caller reach weights; visits and average counts are
never silently converted to reach probabilities. Native average counts normalize
only the per-infoset policy. Ordered-hole infosets collapse to one concrete hand
using explicitly supplied masses, then the reviewed component exports all 169
labels with measured partial coverage. Unknown hands have null policy, EV remains
null everywhere. Postflop contexts and mismatched action sets fail closed.

Observed native fixture: 200 actual trained iterations with seed17, stacks[4,4],
no rake/ante. The fixture explicitly supplies mass1 per selected ordered infoset;
these are synthetic demonstration weights, not recovered actual reach masses.
`observed-native-frequencies.json` stores the resulting real native policies.
No missing hand/policy/EV is invented to obtain complete coverage.

## Exact real-poker policy oracle
`exact_policy_value` clones actual NativeState nodes, traverses a finite legal
policy tree with exact Fraction arithmetic, and enforces an explicit node budget.
Native uniform remaining-card chance is converted to exact 1/N probabilities.
This is policy evaluation, not best response, exploitability or equilibrium.

Independent fixed chip expectations on actual native states:
- Preflop AA versus22, SB1/BB2, explicit fold: net[-1,+1].
- Check/call to board 4c6d8hTcQd: AA wins net[+2,-2].
- Check/call from turn 4c6d8hTc, enumerate44 remaining rivers:
  AA wins42 and loses against the2 remaining deuces, exact net[20/11,-20/11].
These are tiny, known-card native poker subtrees, not full hidden-information
strategy accuracy or a converged GTO solution.

## Fixed pre/post evidence
Feature input b652c04: missing bridge import ERROR1, zero test methods executed.
After implementation:9 unchanged native acceptance tests pass per variant.
Additional input1e9f78c:3 tests execute, one ERROR from unhashable-card TypeError;
the smallest format-ordering fix makes all3 pass, without changing those tests.
Local9+3 tests run in separate Next/Cache/Packed processes (36 PASS), existing18
Python tests and reused33 dependency acceptance pass. CI rebuilds exact pinned
reconstructed modules and repeats these checks. See docs/qa/native-hand169-bridge-20261023/.

## Remaining final-spec work
169 frequency wiring is PARTIAL: context-specific observed policies now connect,
but complete1326 coverage and actual externally justified reach weights remain.
169 EV is PARTIAL: API propagates null because no native EV estimator is present.
Original G9 source/acceptance, authoritative20-stack fixtures, G11 ABI/checkpoint
compatibility, broad rake/ante/size profiles and full-poker convergence remain
BLOCKED/unproved. No strategic correctness is inferred from the small oracle.

Next: validate reach-mass provenance, extend exact small-poker references to
side-pot/rake/ante boundaries, and design a justified native EV estimator. Keep
context identity and explicit unknown values; do not replace missing evidence
with uniform weights or a synthetic strategy claim. No production/main/controller
or scheduler adoption is included.

## Additional native rule-profile QA (not new bug fixes)
Three more hand-derived actual-native fixed-policy oracles run per variant:
- BBante2, stacks4/4:44 rivers yield[41/11,-41/11].
- Cash10%floor rake, two10chip all-ins:44 rivers yield[79/11,-101/11],
  sum=-2 chips, exactly the rake.
- Three-player AA/KK/QQ stacks10/6/2: refund4 and main6+side8 pots,
  42 rivers yield[148/21,-112/21,-12/7], sum=0.
The expectations are derived explicitly in test_poker_oracle_profiles.py and are
not generated from snapshots of the implementation under test. These9 cross-variant
checks extend known-card policy/rule coverage, not GTO equilibrium claims.

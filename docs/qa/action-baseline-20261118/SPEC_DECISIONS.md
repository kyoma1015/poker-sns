# Owner decisions — PENDING, no approval inferred

The existing release proposal is authoritative as a proposal only:
`docs/specs/GTO_PREFLOP_RELEASE_PROPOSAL_20261117.md`.
Questions were submitted to the owner; no answer has been received. Research
continues in isolated HU50/zero-ante/zero-rake without adopting these proposals.

1. **20 stack values:** approve proposed list / provide original list / hold.
   Suggested list: 2,3,4,5,6,7,8,9,10,12,15,20,25,30,40,50,75,100,150,200BB.
   Reason: explicit reproducible coverage; unequal stacks, ICM, MTT/ring assignment
   still require definition. This does not resolve those profile requirements.
2. **Legal sizing grid:** 0.5BB (recommend) / 0.25BB / hold.
   Reason: 0.5BB matches existing native integer-chip research; every legal
   raise-to on the approved grid must be supported, including short all-ins.
3. **Ante/rake profiles:** approve proposal / provide original profiles / hold.
   Proposed BBA 0/1BB, ante-first, stack measured before payment; ring zero-rake
   plus 5%/10% crossed with uncapped/5BB/10BB cap. No-flop-no-drop,
   whole-hand cap, chip-floor rounding, ante rakeable, levy at settlement.
   Reason: explicit settlement allows native/reference expectation checks;
   none of these economic rules may be silently chosen for a formal product.

Approval of a list or grid alone is not approval of all release requirements or
quality thresholds. Formal 12 conditions and existing quality gates are unchanged.

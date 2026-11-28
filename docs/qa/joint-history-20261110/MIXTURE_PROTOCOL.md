# Fixed conservative mixture measurement, before any new population outcome

On both tiny registered games,lambda.25 realization mixture improves the initial
baseline (.006764418→.005589590 and .005129057→.004168435),but less than rawalt.
Deploy only this FIXED lambda.25 (not a population-optimized grid) after coherent
population epoch5 training completes. Blend with immutable frozen0.932107baseline.
This is a separate900seconds read-only evaluation budget,not additional training
or an extension to the existing3600second training/evaluation budget.
Allpopulation epoch4/5 outputs remain; no checkpoint selected by result to mix.
If epoch5 training incomplete, skip mixture and reportNOT_COMPLETED; never blend
half-updated shared preflop state. Input policy hashes must remain unchanged.

Use own sequence realization reach before mixing each information set,not a
pointwise behavioral average. Public-preflop rows share all169classes across all
flops. Postflop depends only on own169/flags and public board/history. Hidden
opponent cards are not used by the policy. Independent ancestor-product,
fixed-opponent payoff-affinity and board-invariance tests mustPASS.

The mixture object holds literal normalized policy numbers for evaluation only;
zeros used as unused regret slots are NOT claimed as learned regret history,
and train() is prohibited. All1755boards/22100flops/9branches use original BR.
Numerical guard1e-8,target0.1BB,formal0/12,normal0 remainunchanged. Adopt only if
FULL independent NC improves frozen by1e-8;otherwisebaseline retained. No further
lambda/seed/board selection or time extension after observing outcomes.
Resource: existing2CPU/8GiB,evalaccumulator only(no2ndlargeDB),diskfree>=4GiB.

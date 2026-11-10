# New vector backend qualification, not a rerun for existing CI

A new exact CF-vector recurrence integrates private chance/opponent reach at
terminals and propagates owner-policy expectations/opponent sums. It removes
N-by-world arrays, preserves own169/flags/public histories, and never prunes or
samples valid chance. BR preflop maximization is still deferred across allboards.
Normalized policy required; memory guard2GiB. Old full/training kernel unchanged,
NOT switched in the registered alternating or mixture run.

Small tests: explicit paths/64pureBR,nonuniformactualtree profiles/current and
average policies,zeroownreach and invalidnormalization. Three real board samples
already pass1e-8 numericalguard with3–4x CPU improvement. These samples are not
whole-population or trueNLHE accuracy evidence.

Before ANY future deployment, compare original and vector outputs on ALL1755
orbits of the immutable frozen fine profile: everygradient,average weight,BRleaf,
metric,preflopaction numerator/denominator; aggregate chance-weightedrootEV/NC and
actionEV. Record everymaximumerror and allpartialfailure. Tolerance1e-8BB. Fixed
900CPU seconds/1500activewall seconds,one finite worker,existingcache,parentDB
read-only,2CPU/8GiB total with the ongoing trainer. Atomic numerical-checkpoint
saves every32boards;budgetresume keeps consumedCPU/wall,never resets previouswork.
This new-backend qualification is distinct from repeating an already successful
old-model evaluation;no original CI rerun. No epochtraining or ordinaryadmission.

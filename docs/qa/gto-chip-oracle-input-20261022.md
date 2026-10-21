# Next reviewed candidate: exact integer chip expectations

This input is prepared for a future scheduled invocation, not implemented here.
At PR61 source b6456dce6e8f468448f2daedc8850dce6d7d76ff, changing eight zero-rake
expectations from integer 0 to JSON false still yields PASS17. Python equality
also treats 0.0 as equal to integer0. The existing fixture contract uses exact
integer chip counts and rounding; truth values/floating amounts are not chip
oracle values. This does not establish a defect in the preserved poker kernels.

Narrow source task: before loading reference/native, validate present known chip
expectation fields. rake/refund must have type int exactly (not bool/float).
net/pot_amounts/pot_rakes must be lists of exact ints. Negative integer net is
valid and must remain so. Missing fields may still be partial expectations;
nonempty expected-object gate stays in force. Leave other supported expectation
fields/comparison behavior, all fixture bytes, original sources and checkpoints
unchanged. Only gto/native/settlement.py may change in the future worker.

Fixed acceptance is the previous22 plus6 new tests, using private synthetic JSON
copies. Preserve valid17 cases and wrong-integer mismatch failure. No kernel
build, dependency install, historical resume, database or network is necessary.
Do not dispatch in the current invocation: C has already completed its one task.

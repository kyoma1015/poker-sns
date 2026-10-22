# Corrected chip-oracle contract — new immutable v2 input

The prior v1 descriptor incorrectly classified refund as a scalar. Its exact
instruction caused5 errors in fixed28: all17 valid source fixtures contain
refund as int[]. Hash-verified preserved Betting.settle constructs
`refund=[0]*self.n`, sets `refund[p]`, and returns that vector. rake is scalar.
The failed v1 source/worktree/protected tests remain preserved and BLOCKED;
there is no successful v1 commit. Do not rewrite or report v1 as PASS.

This separate v2 input corrects the contradiction before new protected hashes
are registered. Only rake is scalar exact int. refund/net/pot_amounts/pot_rakes
are lists of exact ints; bool/float are refused. It adds invalid scalar values
to every vector's tests and a positive partial-refund-vector case, retaining
negative net, valid17, real mismatch, nonempty expectation, rank7 and budgets.
Original fixture/reference/solver/checkpoint bytes are unchanged.

This is the one corrective retry of the same narrow development goal, authorized
by the current user's explicit continue/fix instruction. It is not a scheduled
launch proof and does not alter the existing finite schedule. Only future worker
source path allowed: gto/native/settlement.py. No DB/native build/dependency work.

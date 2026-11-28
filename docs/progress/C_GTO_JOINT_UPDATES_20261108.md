# C joint update audit and fixed-budget comparison

Base508a91b36ed00c6e17dee150122311125a77a486, clean/public checked before edits.
Formal0/12,normal0 unchanged. Frozen/base stream/model/UI/demo not modified.

Independent small-game explicit path products and all64 pure BR policies per
player match original native gradients/own-reach averages/action EV/BR. Asymmetric
correlated public chance and excluded hole pairs included; zero own reach must
not suppress CFregret, zero opponent reach does. Analytic2x2 game equilibrium
p=q=.4,value.2 verifies all schedules. No discrepancy found in this bounded audit;
this is not a proof of all implementations or full NLHE accuracy.

Local9 testsPASS. Initial test failures were a2e-16 exact float equality and a
vanilla analytic matrix exploitability0.042275 at2048 below insufficient test
horizon for fixed0.04 target. Changed float comparison to1e-14 tolerance and
increased analytic-test horizon16384 without relaxing target or solver changes.
These were test assumptions, not production numerical fixes; initial logs retained.

New independent joint_updates schedules and identity-isolated SQLite stores:
vanilla+linear averaging,simultaneousCFR+linear,DCFR(1.5,0,2). Original BR kernel
unchanged; training-only kernel removes unusedBR traversal and its gradients/
averages match bit-for-bit. The old unweighted regret certificate is explicitly
not used to certify discounted/linear averages; exact BR is authoritative.
Protocol/registration stored before workers started,2epochs/checkpoints1,2 each,
7200s perworker,10800s operator,2CPU cgroup/8GiB RAM/newdata8GiB/freeguard4GiB.

Finiteworkers running at /workspace/joint-updates-run; operator command is
PYTHONPATH=. python -B /workspace/run-joint-updates-comparison.py
Do NOT rerun that new-registration command. Resume a partial candidate via
python -B -m gto.abstract.joint_updates --root /workspace/joint-updates-run \
 --method METHOD --cache /workspace/joint-stream-cache \
 --baseline /workspace/joint-stream-run/frozen.sqlite --seconds REMAINING_BUDGET
Read registration/results/sourceidentity/cursor and remaining ORIGINAL budget
first. No background automatic restart exists. Completed candidate must not rerun.

Current results PENDING; no convergence improvement or formal acceptance claimed.
NewheadCI required; successful old508CI not rerun. Existing official20stack/fullsize
source and matched authorized reference still unavailable, real-game errorUNKNOWN.

## Completed results and disclosed extra measurement
All3registered full-population candidates trained3epochs,checkpoint1/2/3 BR now
complete1755/22100. Final NC linear2.473734206798,CFR+4.888656674494,
DCFR3.726963290928BB,allWORSE thanfrozen0.932107;0.1targetFAIL,noadoption.
26localtestsPASS,protected manifestsPASS. First published239f2d40 CI6/6SUCCESS,
806test executions+27browser. Final guard/data/CI-history-depth fix needs newheadCI.
Original7200s cap left third evaluation partial; explicitly registered extra1800s
measurement-only(no training),completed421.565219s wall,all policyhashesunchanged.
Original partial outcomes preserved. Final-source update formulas were not changed
while the experiment ran. Full raw checkpoint JSON is gzip-preserved inQA.
3x4contexts/2028handrows/6084actionEVcells research-only,newUI0/normal0/formal0/12.
The4e-16 report-comparison artifact was fixed with a1e-8 improvement guard.
CI checkout history nowfull so the required old telemetry-transition commit is
available after further descendants; no verification disabled. Baseline remains
best of measured candidates; no completed experiment should be rerun on resume.

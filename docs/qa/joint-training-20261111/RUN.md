# Explicit finite research operation

Example (local research only; never ordinary range publication):

```
python -B -m gto.abstract.joint_training_run \
  --backend vector --overlay /workspace/new-trial/vector.sqlite \
  --parent /workspace/joint-updates-run/cfr_plus.sqlite \
  --cache /workspace/joint-stream-cache --seconds 1800 --epochs 1 \
  --max-blocks 3510 --evaluate
```

Use a different overlay with `--backend legacy` for an explicitly separate
comparison. The parent is the genuine completed same-population epoch3 checkpoint;
no history is fabricated from a policy. Parent must be quiescent. Backend/source/
parent changes reject resume; never overwrite identity to bypass this protection.
Operator lock prevents two runners writing the same overlay. Each invocation is
one new finite budget, not an automatic restart. `--epochs` counts additional
epochs from current checkpoint, not an absolute target. Inspect meta first; never
blindly rerun the registered benchmark (its exact one-epoch budget is separate).
Half owner sweeps are retained but cannot be evaluated as a coherent epoch.
Remaining time includes compilation/initialization, independent originalBR can
stop partial and must retain coverage/EV bounds. Actual caches/DBs stay local and
must not be Git-added. Original5GB recoveryZIP predates these new overlays.

Inspect original budget/protocol and saved state before resuming any interrupted
measurement. Do not reset elapsed budgets or redo already complete evaluations.
Original restricted-game baseline remains0.932107BB; formal0/12,ordinary0.

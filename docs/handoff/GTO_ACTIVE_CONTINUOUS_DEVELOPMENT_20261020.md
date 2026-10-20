# GTO continuous development correction (owner instruction, 2026-10-20)

This document supersedes the GTO wording in docs/handoff/CONTINUOUS_PARALLEL_DELIVERY_POLICY_20261020.md.

## Binding intent
GTO is **ACTIVE CONTINUOUS DEVELOPMENT**, not a parked track or passive preservation task. Advance GTO in parallel with SNS, TDA quiz and player-type diagnosis. GTO must not wait for completion of other lanes. The owner expects steady concrete development progress and no repeated prompting for every small step.

## GTO execution lane
1. Examine docs/progress/C_GTO.md and all handoff artifacts. Establish source and dependency/checkpoint inventory and evidence.
2. Recover or reconstruct vendored G11 dependencies and baseline evidence where legally and technically possible; do not claim missing binaries/checkpoints exist.
3. Run native C++ build and automated tests, fix actual failures, and save logs.
4. Resume solver/checkpoint experiments only when compatible data is available. If blocked, develop independent GTO components, validation harnesses, benchmarks, and tests rather than idling.
5. Create separate development commits and Draft PRs for each meaningful milestone. Continue selecting the next safe work item without waiting for the other three tracks.
6. Preserve full target scope: 2–9 players, 20 stack configurations, ring rake and BB ante, MTT chipEV, required bet sizes, 169-hand frequency/EV. Do not silently reduce specifications.
7. Do not merge to main, deploy to production, change production Supabase, spend money, or overwrite another active GTO branch without explicit approval and passing gates.

## Execution limitation
A repository instruction alone does not launch a persistent Codex worker. Continuous unattended execution requires an explicitly configured runner/automation. Until one is confirmed active, each Codex run should work through multiple successive GTO milestones rather than stopping after a single audit. Report actual work, tests, blockers and next work, never promise work is running when no worker is running.

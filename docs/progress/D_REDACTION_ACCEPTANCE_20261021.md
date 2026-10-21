# D-RESULT-ERROR-REDACTION-01 — trusted input, not implementation

Base PR35:43e2bae1f5de33fc0d94a1d30b974492fbfbf238. Source remains unchanged.
Goal: save/share errors use fixed Japanese retry guidance, never render arbitrary backend exception details. Preserve50-answer retry, multi-click behavior and result-generation guards. Only allowed source src/PlayerTypeDiagnosis.tsx. No scoring/animal/question/SQL/production changes.

Fixed acceptance command: node --test tests/worker-acceptance.test.mjs. Actual baseline Chromium390x844/local-memory/external-blocked:4cases,2PASS/2FAIL. Save and share both leak SYNTHETIC_PRIVATE_DIAGNOSIS_DETAIL into DOM. Gesture and late-save/share isolation already PASS. New tests also require50/50 retry and successful subsequent share once redaction failures are fixed.
Evidence log: /workspace/work/issue22-d-redaction-baseline.log; catalog coordinator will retain this log. No secrets used: marker is a fixed synthetic string.

Dependency contract: Node24, existing locked npm-ci dependencies in a trusted parent node_modules, exact package-lock SHA25688337f40607d439e7c4fcc63160c607e7232b0dd45da30ce03f79f3515165411. Protected acceptance Vite cache uses owned mkdtemp outside worktree and cleans it. Do not npmci/build inside prepared source before finish. CI installs locally on isolated Actions runner and has contents:read/persist-credentials:false.

Risk low, frontend error presentation only. Execution requires current PR/CI overlap review, retained shared state continuity, no active Dlease, formal prepare/dispatch/finish. This input branch must NOT be merged as a feature: its intentionally failing acceptance is only the pinned development baseline. Full implementation acceptance is4PASS and existing diagnosis/mobile/build/lint regression PASS.

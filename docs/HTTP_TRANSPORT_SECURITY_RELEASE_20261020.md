# HTTP transport security-only release candidate — 2026-10-20
Base: main f8890b6ec11d30676c55dc7dc8801f1da8549d28.
This PR does not include PR #13, poll/notification SQL, diagnosis or TDA changes.

## Problem and change
undici 5.28.4 is pinned by @vercel/node 23.0.1 (development tooling) and also satisfies OpenAI's optional >=5 <9 peer, so npm classifies it and @fastify/busboy as production dependencies. The production audit had high 2. Even @vercel/node 25.0.0 still pins the old version; npm audit fix dry-run did not update it.
Pin an explicit override undici=6.29.1. The production dependency audit now has 0 vulnerabilities and the unused vulnerable busboy dependency disappears. This is an intentional major-version transitive override; it is not an upstream Vercel release. Node minimum is >=18.17; CI uses Node 24.

## Verification
- npm ci, npm run build and npm run lint: PASS (pre-existing warnings remain).
- npm audit --omit=dev --json: total/high/critical 0.
- node tests/http-transport.test.mjs: 3 PASS. Exercises Vercel-dev-server's imported Headers/request APIs, fetch JSON, OpenAI responses with a supplied mocked fetch. Undici MockAgent disables all real connections; there were no paid API calls or DB calls.
- No app TSX changes: browser UI behavior is unaffected by this dependency-only patch; actual Vercel deployment runtime must still be observed by the release coordinator.
- Full audit still finds development-tooling high 8 / moderate 1 (Vercel/ts-morph/braces/path-to-regexp/ajv chain). This is not a claim that all dependencies are vulnerability-free. Application API imports @vercel/node types only; OpenAI uses global/custom fetch. Build/dev tooling advisory reachability has not been proved harmless.
Logs and audit evidence: docs/qa/http-security-release-20261020/.

## Release / rollback
No main merge, deployment or Supabase operation performed by this lane.
Release coordinator must verify CI and deployment environment/authorization, then can consider this independently of PR #13's DB gates.
Rollback: revert this dependency-only commit, reinstall from lock and redeploy prior artifact. Reverting restores known vulnerable dependency versions; do not treat rollback as a safe permanent security state. No DB rollback is required.

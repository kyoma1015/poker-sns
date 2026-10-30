# Dedicated cloud client checkpoint
Acceptance before changes: reject mixed production/test endpoint, missing opt-in, wrong site origin, public privileged env keys and release-flag reuse before persisted Auth initialization, reservation/finalize/media requests and Storage upload.
Startup guard in src/supabase.ts covers Timeline's shared client. Explicit guards repeat before video API calls and immediately before upload.
This remains a deny-first checkpoint: existing VIDEO_SERVER_ENABLED default and recovery client false are unchanged. No cloud enable path, schema, allowlist, keys or deployment have been provisioned. Guard tests are configuration and source-order regressions, not Chromium cloud E2E.

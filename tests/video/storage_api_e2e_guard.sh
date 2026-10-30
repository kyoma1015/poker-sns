#!/usr/bin/env bash
# Guard against accidentally treating SQL-only QA as Storage API E2E.
set -euo pipefail
if [[ -n "${SUPABASE_URL:-}" || -n "${SUPABASE_SERVICE_ROLE_KEY:-}" || -n "${VITE_SUPABASE_URL:-}" ]]; then
  echo 'BLOCKED: inherited Supabase credentials; refusing Storage QA' >&2
  exit 2
fi
echo 'BLOCKED: no ephemeral local Supabase Storage API stack or Auth fixtures provisioned' >&2
echo 'NOT RUN: owner upload, viewer access, signed URL, HTTP 20MiB rejection, orphan cleanup' >&2
exit 2

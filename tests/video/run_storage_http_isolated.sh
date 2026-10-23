#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
for k in SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY VITE_SUPABASE_URL SUPABASE_DB_URL; do
 if [[ -n "${!k:-}" ]]; then echo "BLOCKED: inherited $k"; exit 2; fi
done
export DOCKER_HOST=unix:///var/run/docker.sock
unset DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
qa="$(mktemp -d)"
trap 'npx --yes supabase@2.81.3 stop --workdir tests/video/local-stack --no-backup >/dev/null 2>&1 || true; rm -rf "$qa"' EXIT
npx --yes supabase@2.81.3 start --workdir tests/video/local-stack --exclude studio,imgproxy,mailpit,edge-runtime,realtime,vector,logflare
npx --yes supabase@2.81.3 status --workdir tests/video/local-stack -o env > "$qa/local.env"
apiurl="$(sed -n 's/^API_URL=//p' "$qa/local.env" | tr -d '\"')"
[[ "$apiurl" == 'http://127.0.0.1:56321' ]] || { echo 'BLOCKED: unexpected API endpoint'; exit 2; }
dburl="$(grep '^DB_URL=' "$qa/local.env" | cut -d= -f2- | tr -d '"')"
[[ "$dburl" == *"127.0.0.1:56322"* ]] || { echo 'BLOCKED: unexpected DB endpoint'; exit 2; }
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/storage_bootstrap.sql
psql "$dburl" -v ON_ERROR_STOP=1 -f sql/post_short_videos_candidate.sql
VIDEO_QA_ENV="$qa/local.env" node tests/video/storage_http_e2e.mjs

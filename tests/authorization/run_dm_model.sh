#!/usr/bin/env bash
set -euo pipefail
# No URL/credentials/volume mounts/ports accepted. Only a new network-isolated container.
model_container="abd-dm-model-${GITHUB_RUN_ID:-local}-${RANDOM}"
cleanup() { timeout 20s docker rm -f "$model_container" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run -d --name "$model_container" --network none --memory 512m --cpus 1 \
 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17 >/dev/null
ready=0
for attempt in {1..30}; do
 if docker exec "$model_container" pg_isready -U postgres >/dev/null 2>&1; then ready=1; break; fi
 sleep 1
done
[ "$ready" = 1 ] || { echo 'BLOCKED: disposable Postgres startup'; exit 1; }
sql() { timeout 60s docker exec -i "$model_container" psql -X -qAt -v ON_ERROR_STOP=1 -U postgres; }
sql < tests/authorization/dm_model_setup.sql
sql < tests/authorization/dm_weak_model_reproduction.sql
baseline_log="$(mktemp)"
trap 'rm -f "$baseline_log"; cleanup' EXIT
if sql < tests/authorization/dm_model_acceptance.sql >"$baseline_log" 2>&1; then
 echo 'FAIL: deliberately weak model unexpectedly passed'; exit 1
fi
grep -q 'FAIL:UPDATE_CONTENT_GRANTED' "$baseline_log"
echo 'EXPECTED_BASELINE_FAIL: broad UPDATE grant survives recipient-only RLS'
sql < tests/authorization/dm_policy_candidate.sql
result_log="$(mktemp)"
trap 'rm -f "$baseline_log" "$result_log"; cleanup' EXIT
sql < tests/authorization/dm_model_acceptance.sql | tee "$result_log"
test "$(grep -c '^PASS:' "$result_log")" = 20
echo 'DM_MODEL:20 PASS/0 FAIL; synthetic schema and identity, NOT authentic DM/Supabase/JWT/RPC proof'

#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Always target the managed LOCAL daemon; never an inherited remote Docker host.
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
qa_compose=(docker compose -f tests/polls/docker-compose.yml)
mkdir -p docs/qa/issue22-polls-20261020
cleanup() { "${qa_compose[@]}" logs --no-color > docs/qa/issue22-polls-20261020/docker.log 2>&1 || true; "${qa_compose[@]}" down --volumes; }
trap cleanup EXIT
"${qa_compose[@]}" up -d --wait
for sql_file in tests/polls/bootstrap_fixture.sql tests/polls/legacy_schema_fixture.sql sql/poll_only/forward_candidate.sql sql/poll_only/schedule_candidate.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
python tests/polls/verify_isolated.py

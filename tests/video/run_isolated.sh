#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
name="pokerid-video-qa-$$"
if docker inspect "$name" >/dev/null 2>&1; then echo "BLOCKED: container collision"; exit 2; fi
cleanup() { docker rm -f "$name" >/dev/null 2>&1 || true; }
trap cleanup EXIT
docker run -d --name "$name" -e POSTGRES_PASSWORD=video-fixture-only postgres:17 >/dev/null
ready=0
for i in $(seq 1 90); do
  if docker exec "$name" psql -U postgres -d postgres -Atqc 'select 1' 2>/dev/null | grep -qx 1; then
    ready=1
    break
  fi
  sleep 1
done
if [[ "$ready" != 1 ]]; then echo 'BLOCKED: isolated PostgreSQL not ready'; exit 2; fi
for i in $(seq 1 10); do
  if docker exec "$name" psql -U postgres -d postgres -Atqc 'select 1' 2>/dev/null | grep -qx 1; then break; fi
  sleep 1
done
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/fixture.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < sql/post_short_videos_candidate.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/assertions.sql
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 < tests/video/isolated_insert_once_storage.sql
echo 'PASS: isolated PostgreSQL schema, owner-only RLS, legacy delete and insert-once mutation denial'
echo 'NOT TESTED: Supabase Storage API, signed URLs, media duration, upload cleanup'

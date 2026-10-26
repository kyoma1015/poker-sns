#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
for k in SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY VITE_SUPABASE_URL SUPABASE_DB_URL; do
 if [[ -n "${!k:-}" ]]; then echo "BLOCKED: inherited $k"; exit 2; fi
done
node tests/video/video_privileged_key_static_guard.mjs
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
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_finalize_db.sql
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_finalize_db_qa.sql
VIDEO_QA_ENV="$qa/local.env" node tests/video/storage_http_e2e.mjs
VIDEO_QA_ENV="$qa/local.env" python3 -m tests.video.isolated_finalize_http_e2e
VIDEO_QA_ENV="$qa/local.env" python3 -m tests.video.isolated_cleanup_worker_e2e

VIDEO_QA_ENV="$qa/local.env" python3 -m tests.video.isolated_viewer_signing_e2e

# Isolated QA mutation policy is removed only after all cleanup tests complete.
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_immutable_storage_guard.sql
# Compose the production-oriented immutable policy with existing isolated QA
# INSERT/SELECT policies; no client UPDATE or DELETE should become possible.
# Apply the reservation ledger before the reservation-fenced INSERT policy.
psql "$dburl" -v ON_ERROR_STOP=1 -f sql/video_permanent_key_reservation_review_only.sql
psql "$dburl" -v ON_ERROR_STOP=1 -f sql/post_short_videos_immutable_review_only.sql
VIDEO_QA_ENV="$qa/local.env" node tests/video/isolated_immutable_storage_http_e2e.mjs
# Enforce the single reserved-key writer only after legacy mutation tests.
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_enforce_reserved_writers.sql
# Exercise production-candidate quota RPC in the disposable local DB only.
bash tests/video/isolated_reservation_quota.sh "$dburl"
VIDEO_QA_ENV="$qa/local.env" node tests/video/isolated_reserved_writer_http_e2e.mjs

# Real isolated Auth + Storage HTTP + PostgREST RPC + ffprobe composition.
# The immutable Storage guard is active before the generation-fenced RPC runs.
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_fenced_publish.sql
# The actual Chromium uploader now reserves each key through the trusted RPC.
# Apply the append-only ledger only to this disposable local stack.
psql "$dburl" -v ON_ERROR_STOP=1 -c "notify pgrst, 'reload schema';"
# Node 24 strips TS but does not resolve runtime .js specifiers to source .ts.
# Use ephemeral aliases only in isolated QA; never commit generated .js files.
for source in api/video-*.ts; do
  ln -s "$(basename "$source")" "${source%.ts}.js"
done
trap 'for source in api/video-*.ts; do rm -f -- "${source%.ts}.js"; done; npx --yes supabase@2.81.3 stop --workdir tests/video/local-stack --no-backup >/dev/null 2>&1 || true; rm -rf "$qa"' EXIT
VIDEO_QA_ENV="$qa/local.env" node tests/video/isolated_fenced_real_e2e.mjs
# Production attestation candidate is applied ONLY to the disposable local DB.
# Never reuse these fixture credentials or enable the production release gate.
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/isolated_attested_generation.sql
psql "$dburl" -v ON_ERROR_STOP=1 -f tests/video/production_attested_candidate_review_only.sql
psql "$dburl" -v ON_ERROR_STOP=1 -c "insert into video_private.attestation_keys(key_id,secret,active) values(1,decode(repeat('41',32),'hex'),true),(2,decode(repeat('42',32),'hex'),true); grant execute on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated; notify pgrst, 'reload schema';"
VIDEO_QA_ENV="$qa/local.env" node tests/video/isolated_attested_real_http_e2e.mjs

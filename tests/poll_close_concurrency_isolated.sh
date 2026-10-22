#!/usr/bin/env bash
set -Eeuo pipefail
c=poll-close-concurrency-synthetic
cleanup() {
  status=$?
  trap - EXIT
  docker rm -f "$c" >/dev/null 2>&1 || true
  if docker inspect "$c" >/dev/null 2>&1; then
    echo '::error::Container cleanup failed'; status=1
  else echo 'PASS: container cleanup'; fi
  exit "$status"
}
trap cleanup EXIT
echo 'DIAG: host memory and container availability (no secrets)'
free -m || true
docker info --format 'Docker memory bytes={{.MemTotal}}' || true
docker run -d --name "$c" --network none --memory 2g --memory-swap 2g \
  -e POSTGRES_PASSWORD=synthetic_only_not_a_secret \
  supabase/postgres:17.11.0.004 postgres -D /etc/postgresql \
  -c max_connections=25 \
  -c shared_buffers=32MB -c work_mem=2MB -c maintenance_work_mem=16MB >/dev/null
echo 'DIAG: container launched'
ready=0
for i in $(seq 1 90); do
  if docker exec "$c" pg_isready -U postgres -d postgres >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
if test "$ready" -ne 1; then
  docker inspect "$c" --format 'DIAG: status={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' || true
  docker logs "$c" 2>&1 | tail -25 || true
  exit 1
fi
docker inspect "$c" --format 'DIAG: status={{.State.Status}} oom={{.State.OOMKilled}}' || true
echo 'DIAG: initial database ready; allow Supabase image init restart to settle'
sleep 8
if ! docker exec "$c" pg_isready -U postgres -d postgres >/dev/null 2>&1; then echo '::error::Postgres unavailable after init settle'; exit 1; fi
echo 'DIAG: post-init database ready'
q() { docker exec "$c" psql -X -At -U supabase_admin -d postgres -v ON_ERROR_STOP=1 -c "$1"; }
docker exec -i "$c" psql -X -q -U supabase_admin -d postgres -v ON_ERROR_STOP=1 < tests/poll_close_concurrency_fixture.sql
echo 'DIAG: fixture loaded'
# Extract and execute the production-candidate function definition verbatim.
# Fail closed if the marker, ending or expected signature changes.
python3 - <<'PY'
from pathlib import Path
src=Path('sql/poll_only/forward_candidate.sql').read_text()
start='create or replace function poll_private.close_due_polls() returns integer'
end='revoke all on function poll_private.close_due_polls()'
assert src.count(start)==1 and src.count(end)==1
body=src[src.index(start):src.index(end)]
assert body.strip().endswith('end $$;')
Path('/tmp/poll-close-real-function.sql').write_text(body)
print('PASS: exact production-candidate function extracted')
PY
docker exec -i "$c" psql -X -q -U supabase_admin -d postgres -v ON_ERROR_STOP=1 < /tmp/poll-close-real-function.sql
echo 'DIAG: real function installed'
# Make first invocation hold a notification INSERT so the second connection
# must encounter an already-locked poll row (SKIP LOCKED).
q 'update public.synthetic_controls set delay_seconds=4' >/dev/null
docker exec "$c" psql -X -At -U supabase_admin -d postgres -v ON_ERROR_STOP=1 -c 'select poll_private.close_due_polls()' > /tmp/poll-close-a.out 2>/tmp/poll-close-a.err &
p1=$!
sleep 1
docker exec "$c" psql -X -At -U supabase_admin -d postgres -v ON_ERROR_STOP=1 -c 'select poll_private.close_due_polls()' > /tmp/poll-close-b.out 2>/tmp/poll-close-b.err &
p2=$!
if ! wait "$p1"; then sed -E "s/[[:xdigit:]]{32,}/[REDACTED]/g" /tmp/poll-close-a.err; docker inspect "$c" --format "DIAG: container={{.State.Status}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}}" || true; docker logs "$c" 2>&1 | tail -35 | sed -E "s/[[:xdigit:]]{64}/[REDACTED]/g" || true; exit 1; fi
if ! wait "$p2"; then sed -E "s/[[:xdigit:]]{32,}/[REDACTED]/g" /tmp/poll-close-b.err; exit 1; fi
test "$(q "select count(*) from public.notifications where type='poll_closed'")" = 3
test "$(q "select count(*) from poll_private.close_receipts")" = 2
test "$(q "select count(distinct user_id) from public.notifications where type='poll_closed'")" = 3
test "$(q "select count(*) from poll_private.close_receipts where post_id=(select id from public.synthetic_ids where label='legacy')")" = 0
test "$(q "select poll_private.close_due_polls()")" = 0
echo 'PASS: concurrent connections, distinct owners, old notification suppression, no duplicates'
# Failure must roll back the receipt together with the attempted notification.
q 'update public.synthetic_controls set delay_seconds=0, fail=false' >/dev/null
q "insert into public.synthetic_ids values ('retry','10000000-0000-4000-8000-000000000004','20000000-0000-4000-8000-000000000004')" >/dev/null
q "insert into public.posts select id,owner_id from public.synthetic_ids where label='retry'" >/dev/null
q "insert into public.post_interactive select id,'poll',clock_timestamp()-interval '1 hour' from public.synthetic_ids where label='retry'" >/dev/null
q 'update public.synthetic_controls set fail=true' >/dev/null
if q 'select poll_private.close_due_polls()' >/tmp/poll-close-failure.out 2>/tmp/poll-close-failure.err; then
  echo '::error::Expected notification INSERT to fail'; exit 1
fi
test "$(q 'select count(*) from poll_private.close_receipts')" = 2
test "$(q "select count(*) from public.notifications where type='poll_closed'")" = 3
q 'update public.synthetic_controls set fail=false' >/dev/null
test "$(q 'select poll_private.close_due_polls()')" = 1
test "$(q 'select poll_private.close_due_polls()')" = 0
test "$(q 'select count(*) from poll_private.close_receipts')" = 3
test "$(q "select count(*) from public.notifications where type='poll_closed'")" = 4
echo 'PASS: INSERT failure atomic rollback and exactly-once retry'
echo 'BLOCKED: production backup, restore, Vault keys and live cron cutover'

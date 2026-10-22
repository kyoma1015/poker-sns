#!/usr/bin/env bash
set -Eeuo pipefail
c=poll-cron-cutover-synthetic
cleanup() {
  status=$?
  trap - EXIT
  docker rm -f "$c" >/dev/null 2>&1 || true
  if docker inspect "$c" >/dev/null 2>&1; then
    echo '::error::Synthetic container was not removed'
    status=1
  else
    echo 'PASS: synthetic container removed'
  fi
  exit "$status"
}
trap cleanup EXIT
docker run -d --name "$c" --network none -e POSTGRES_PASSWORD=synthetic_only_not_a_secret \
  supabase/postgres:17.11.0.004 postgres -D /etc/postgresql \
  -c shared_preload_libraries=pg_cron,pgsodium,supabase_vault \
  -c cron.database_name=postgres -c cron.use_background_workers=on >/dev/null
ready=0
for i in $(seq 1 90); do
  if docker exec "$c" pg_isready -U postgres -d postgres >/dev/null 2>&1; then ready=1; break; fi
  sleep 1
done
test "$ready" -eq 1
psqlq() { docker exec "$c" psql -X -At -U supabase_admin -d postgres -v ON_ERROR_STOP=1 -c "$1"; }
psqlfile() { docker exec -i "$c" psql -X -q -U supabase_admin -d postgres -v ON_ERROR_STOP=1 < "$1"; }
psqlfile tests/poll_cron_cutover_fixture.sql
# Fixed FAIL: the unmodified schedule_candidate must reject the old scheduler.
if psqlfile sql/poll_only/schedule_candidate.sql >/dev/null 2>&1; then
  echo '::error::Schedule accepted overlapping legacy cron'
  exit 1
fi
test "$(psqlq "select count(*) from cron.job where jobname='poker_id_poll_closed_notifications'")" = 1
test "$(psqlq "select count(*) from cron.job where jobname='pokerid-poll-close-v1'")" = 0
echo 'PASS: existing scheduler blocks new scheduler without modifying data'
# Verify actual in-flight legacy execution; never simulate drain by deleting job_run_details.
running=0
for i in $(seq 1 25); do
  n="$(psqlq "select count(*) from cron.job_run_details where status='running' and command like '%poll_synthetic_legacy%'")"
  if test "$n" -gt 0; then running=1; break; fi
  sleep 1
done
test "$running" -eq 1
psqlq "select cron.unschedule('poker_id_poll_closed_notifications')" >/dev/null
if psqlfile sql/poll_only/schedule_candidate.sql >/dev/null 2>&1; then
  echo '::error::Schedule accepted running legacy invocation'
  exit 1
fi
echo 'PASS: unschedule does not bypass in-flight drain guard'
drained=0
for i in $(seq 1 35); do
  n="$(psqlq "select count(*) from cron.job_run_details where status='running' and command like '%poll_synthetic_legacy%'")"
  if test "$n" = 0; then drained=1; break; fi
  sleep 1
done
test "$drained" -eq 1
psqlfile sql/poll_only/schedule_candidate.sql
test "$(psqlq "select count(*) from cron.job where jobname='pokerid-poll-close-v1'")" = 1
test "$(psqlq "select count(*) from cron.job where jobname='poker_id_poll_closed_notifications'")" = 0
psqlq "select poll_private.close_due_polls(); select poll_private.close_due_polls();" >/dev/null
test "$(psqlq 'select count(*) from poll_fixture.receipts')" = 1
echo 'PASS: drained cutover has exactly one scheduler and idempotent close receipt'
# Actual emergency disable SQL, no changes to source SQL.
psqlfile sql/poll_only/disable_candidate.sql
test "$(psqlq "select count(*) from cron.job where jobname in ('pokerid-poll-close-v1','poker_id_poll_closed_notifications')")" = 0
test "$(psqlq "select has_function_privilege('anon','public.get_interactive_results_v4()','EXECUTE')")" = f
test "$(psqlq "select has_function_privilege('authenticated','public.get_interactive_results_v4()','EXECUTE')")" = f
test "$(psqlq 'select count(*) from poll_fixture.votes')" = 2
test "$(psqlq 'select count(*) from poll_fixture.receipts')" = 1
echo 'PASS: emergency disable revokes client RPCs, unschedules jobs, preserves votes and receipts'
# Re-enable requires deliberate role and scheduler grants, not just rescheduling.
psqlq 'grant execute on function public.get_interactive_results_v4() to anon,authenticated' >/dev/null
test "$(psqlq "select has_function_privilege('anon','public.get_interactive_results_v4()','EXECUTE')")" = t
psqlfile sql/poll_only/schedule_candidate.sql
test "$(psqlq "select count(*) from cron.job where jobname='pokerid-poll-close-v1'")" = 1
psqlfile sql/poll_only/disable_candidate.sql
echo 'PASS: explicit re-enable and second emergency disable'
# New boundary: a cron invocation that raises an exception must record failure,
# preserve committed fixture data, and permit a deliberate idempotent retry.
psqlq "create or replace function public.poll_synthetic_failing() returns void language plpgsql as \\\$\\\$ begin raise exception 'synthetic expected failure'; end \\\$\\\$" >/dev/null
psqlq "select cron.schedule('poll-synthetic-fail-retry','5 seconds','select public.poll_synthetic_failing();')" >/dev/null
failed=0
for i in $(seq 1 25); do
  n="$(psqlq "select count(*) from cron.job_run_details where status='failed' and command like '%poll_synthetic_failing%'")"
  if test "$n" -gt 0; then failed=1; break; fi
  sleep 1
done
test "$failed" -eq 1
psqlq "select cron.unschedule('poll-synthetic-fail-retry')" >/dev/null
test "$(psqlq 'select count(*) from poll_fixture.votes')" = 2
test "$(psqlq 'select count(*) from poll_fixture.receipts')" = 1
psqlq 'select poll_private.close_due_polls(); select poll_private.close_due_polls();' >/dev/null
test "$(psqlq 'select count(*) from poll_fixture.receipts')" = 1
echo 'PASS: cron failure recorded; fixture preserved; retry remains idempotent'
# After emergency disable, no public/anon/authenticated EXECUTE on the private worker.
for role in PUBLIC anon authenticated; do
  test "$(psqlq "select has_function_privilege('$role','poll_private.close_due_polls()','EXECUTE')")" = f
done
test "$(psqlq "select has_schema_privilege('anon','poll_private','USAGE')")" = f
test "$(psqlq "select has_schema_privilege('authenticated','poll_private','USAGE')")" = f
echo 'PASS: private worker execution and schema usage remain denied after disable'
echo 'BLOCKED: production scheduler drain, actual production keys, real backup and isolated restore'

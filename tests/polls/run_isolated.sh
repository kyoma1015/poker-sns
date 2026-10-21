#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Always target the managed LOCAL daemon; never an inherited remote Docker host.
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
# Refuse a collision BEFORE installing any cleanup trap: never remove a prior
# developer/agent's containers, network, volume or test data.
for qa_container in pokerid-poll-qa-db pokerid-poll-qa-rest; do
  if docker inspect "$qa_container" >/dev/null 2>&1; then
    echo "BLOCKED: existing $qa_container; no automatic deletion" >&2
    exit 2
  fi
done
if docker network inspect pokerid-poll-isolated_default >/dev/null 2>&1; then
  echo "BLOCKED: existing test project network; no automatic deletion" >&2
  exit 2
fi
export POLL_QA_RUN_ID="poll-qa-$(date +%s)-$$"
qa_compose=(docker compose -f tests/polls/docker-compose.yml)
mkdir -p docs/qa/issue22-polls-20261020
cleanup() {
  qa_exit=$?
  "${qa_compose[@]}" logs --no-color > docs/qa/issue22-polls-20261020/docker.log 2>&1 || true
  if [ "$qa_exit" -ne 0 ]; then tail -n 100 docs/qa/issue22-polls-20261020/docker.log >&2; fi
  for qa_container in pokerid-poll-qa-db pokerid-poll-qa-rest; do
    if docker inspect "$qa_container" >/dev/null 2>&1; then
      qa_owner=$(docker inspect --format '{{index .Config.Labels "pokerid.qa.run-id"}}' "$qa_container")
      if [ "$qa_owner" != "$POLL_QA_RUN_ID" ]; then
        echo "BLOCKED cleanup: resource ownership changed" >&2
        return
      fi
    fi
  done
  "${qa_compose[@]}" down --volumes
}
trap cleanup EXIT
"${qa_compose[@]}" up -d --wait db
# Only the reserved-role local password setup uses the official image admin.
# Application fixtures and reviewed candidate continue to run as postgres.
docker exec -i pokerid-poll-qa-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 < tests/polls/authenticator_fixture.sql
docker exec -i pokerid-poll-qa-db psql -U supabase_admin -d postgres -v ON_ERROR_STOP=1 < tests/polls/official_auth_functions_fixture.sql
for sql_file in tests/polls/bootstrap_fixture.sql tests/polls/legacy_schema_fixture.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
# Fresh fixture has a preserved question. Add a TEST-ONLY old poll with an
# unknown privacy mode and prove the candidate fails transactionally.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
insert into public.posts(id,user_id,content) values('20000000-0000-0000-0000-000000000099','10000000-0000-0000-0000-000000000001','unknown privacy fixture');
insert into public.post_interactive(post_id,kind,options,closes_at) values('20000000-0000-0000-0000-000000000099','poll','["A","B"]',now()+interval '1 hour');
SQL
if docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/forward_candidate.sql > docs/qa/issue22-polls-20261020/unknown-privacy-guard.log 2>&1; then
  echo "FAIL: unknown historical privacy was accepted" >&2
  exit 1
fi
grep -q 'unknown historical privacy' docs/qa/issue22-polls-20261020/unknown-privacy-guard.log
# This deletes only the two synthetic rows inserted just above, never original
# question rows or any developer database. The whole database is a fresh fixture.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $$begin
 if exists(select 1 from information_schema.columns where table_schema='public' and table_name='post_interactive' and column_name='is_anonymous') then raise exception 'Failed guard left partial DDL'; end if;
end$$;
delete from public.posts where id='20000000-0000-0000-0000-000000000099';
SQL
# Validate poll core separately, twice for idempotency, before installing any
# notification worker or scheduler. The disposable DB retains legacy fixtures.
for core_pass in 1 2; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/core_without_notifications_candidate.sql
done
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $core_check$
begin
 if to_regprocedure('public.create_interactive_post_v4(text,text,text[],integer,boolean,text)') is null then
  raise exception 'Core poll creation RPC missing';
 end if;
 if to_regprocedure('poll_private.close_due_polls()') is not null then
  raise exception 'Core unexpectedly installed notification worker';
 end if;
 if exists(select 1 from pg_trigger where tgname='poll_closed_guard_v1' and not tgisinternal) then
  raise exception 'Core unexpectedly installed notification trigger';
 end if;
 if exists(select 1 from cron.job where jobname='pokerid-poll-close-v1') then
  raise exception 'Core unexpectedly installed notification cron';
 end if;
end
$core_check$;
SQL
for sql_file in sql/poll_only/forward_candidate.sql sql/poll_only/forward_candidate.sql sql/poll_only/schedule_candidate.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
# Check that migration replaced the production legacy overloads in-place and
# did not leave public legacy result endpoints callable by authenticated users.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $legacy_rpc_check$
declare r record;
begin
 if to_regprocedure('public.create_interactive_post_v3(text,text,text[],integer,boolean)') is null then
  raise exception 'Production five-argument v3 creation RPC missing';
 end if;
 if to_regprocedure('public.create_interactive_post_v3(text,text,text[],integer,boolean,text)') is not null then
  raise exception 'Unexpected six-argument v3 overload';
 end if;
 for r in select p.oid,p.proname,p.prosecdef from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
  where ns.nspname='public' and p.proname in ('get_interactive_results_v2','get_interactive_results_v3') loop
  if r.prosecdef then raise exception 'Legacy results RPC remains SECURITY DEFINER: %',r.proname; end if;
  if has_function_privilege('authenticated',r.oid,'EXECUTE') then raise exception 'Legacy results RPC still executable: %',r.proname; end if;
 end loop;
end
$legacy_rpc_check$;
SQL
# Reproduce the production scheduler collision in the isolated database.
# A synthetic legacy cron is created ONLY in this disposable QA instance.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
select cron.schedule('poker_id_poll_closed_notifications', '* * * * *', 'select public.dispatch_poll_closed_notifications();');
SQL
if docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/schedule_candidate.sql > docs/qa/issue22-polls-20261020/cron-collision-guard.log 2>&1; then
  echo "FAIL: scheduler accepted concurrent legacy poll notification cron" >&2
  exit 1
fi
grep -q 'Existing interactive cron requires review' docs/qa/issue22-polls-20261020/cron-collision-guard.log
# The refused migration must not have removed either existing job.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $cron_guard$
begin
 if (select count(*) from cron.job where jobname in ('pokerid-poll-close-v1','poker_id_poll_closed_notifications')) <> 2 then
  raise exception 'Scheduler collision guard changed existing jobs';
 end if;
end
$cron_guard$;
select cron.unschedule(jobid) from cron.job where jobname='poker_id_poll_closed_notifications';
SQL
"${qa_compose[@]}" up -d --wait rest
python tests/polls/verify_isolated.py
# Verify the feature-disable rollback against the same disposable DB, twice.
# This must preserve historical questions/answers and remove only our cron.
for rollback_pass in 1 2; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/disable_candidate.sql
done
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $rollback_check$
declare n integer;
begin
 select count(*) into n from public.post_interactive where post_id='20000000-0000-0000-0000-000000000001' and kind='question';
 if n <> 1 then raise exception 'Rollback lost historical question'; end if;
 select count(*) into n from public.post_interactive_responses where post_id='20000000-0000-0000-0000-000000000001' and answer='historical answer fixture';
 if n <> 1 then raise exception 'Rollback lost historical answer'; end if;
 if exists(select 1 from cron.job where jobname='pokerid-poll-close-v1') then raise exception 'Rollback retained new scheduler'; end if;
 if to_regclass('poll_private.close_receipts') is null then raise exception 'Rollback removed private close receipts'; end if;
 if not exists(select 1 from pg_policies where schemaname='public' and tablename='notifications' and policyname='poll_closed_forgery_guard_v1') then raise exception 'Rollback removed notification guard'; end if;
 if exists(select 1 from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='public' and p.proname in ('get_interactive_results_v2','get_interactive_results_v3') and has_function_privilege('authenticated',p.oid,'EXECUTE')) then raise exception 'Rollback exposed historical results RPC'; end if;
end
$rollback_check$;
SQL


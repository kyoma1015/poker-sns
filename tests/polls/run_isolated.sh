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
# Recreate verified production schema/policy/dispatcher deltas in disposable DB.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < tests/polls/production_catalog_parity_fixture.sql
# Assert the legacy RPC contracts before core creates the new v4 endpoint.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < tests/polls/live_rpc_contract_assertions.sql
# Confirm core can be installed over production-like existing privacy columns.
# Validate poll core separately, twice for idempotency, before installing any
# notification worker or scheduler. The disposable DB retains legacy fixtures.
for core_pass in 1 2; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/core_without_notifications_candidate.sql
done
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $core_check$
declare has_new_cron boolean := false;
begin
 if to_regprocedure('public.create_interactive_post_v4(text,text,text[],integer,boolean,text)') is null then
  raise exception 'Core poll creation RPC missing';
 end if;
 if pg_get_function_result('public.create_interactive_post_v4(text,text,text[],integer,boolean,text)'::regprocedure) <> 'uuid' then
  raise exception 'Core poll creation RPC return signature mismatch';
 end if;
 if to_regprocedure('poll_private.close_due_polls()') is not null then
  raise exception 'Core unexpectedly installed notification worker';
 end if;
 if exists(select 1 from pg_trigger where tgname='poll_closed_guard_v1' and not tgisinternal) then
  raise exception 'Core unexpectedly installed notification trigger';
 end if;
 if to_regclass('cron.job') is not null then
  if exists(select 1 from pg_catalog.pg_class c join pg_catalog.pg_namespace n on n.oid=c.relnamespace
    where n.nspname='cron' and c.relname='job') then
   -- pg_cron is not necessarily installed until schedule_candidate.sql.
   execute 'select exists(select 1 from cron.job where jobname=''pokerid-poll-close-v1'')' into has_new_cron;
   if has_new_cron then raise exception 'Core unexpectedly installed notification cron'; end if;
  end if;
 end if;
end
$core_check$;
SQL
# Recheck unchanged RPC return contracts and legacy dispatcher after core.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < tests/polls/live_rpc_contract_assertions.sql
# Install non-destructive legacy question guard twice to prove idempotency.
for guard_pass in 1 2; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/block_legacy_question_inserts_candidate.sql
done
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $guard_check$
begin
 if not exists(select 1 from pg_trigger where tgname='reject_new_question_interactive' and not tgisinternal) then
  raise exception 'Question insert guard missing';
 end if;
end
$guard_check$;
SQL
# Verify historical question survives and legacy question INSERT is rejected.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $guard_behavior$
declare v_existing int;
begin
 select count(*) into v_existing from public.post_interactive where kind='question';
 if v_existing < 1 then raise exception 'Historical question fixture was lost'; end if;
 begin
  insert into public.post_interactive(post_id,kind,options)
  values ('20000000-0000-0000-0000-000000000099','question','[]'::jsonb);
  raise exception 'Question INSERT unexpectedly succeeded';
 exception when sqlstate '22023' then null;
 end;
end
$guard_behavior$;
SQL
# Model a closed production poll already notified by the old dispatcher:
# no poll_private receipt exists for these legacy notifications.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
insert into public.posts(id,user_id,content) values
 ('20000000-0000-0000-0000-000000000098','10000000-0000-0000-0000-000000000001','previously closed poll');
insert into public.post_interactive(post_id,kind,options,closes_at,is_anonymous) values
 ('20000000-0000-0000-0000-000000000098','poll','["A","B"]',now()-interval '1 day',true);
insert into public.notifications(id,user_id,actor_id,type,post_id) values
 ('30000000-0000-0000-0000-000000000098','10000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','poll_closed','20000000-0000-0000-0000-000000000098');
SQL
for sql_file in sql/poll_only/forward_candidate.sql sql/poll_only/forward_candidate.sql sql/poll_only/schedule_candidate.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
# Legacy notices must not be resent by the new closer, even on retry.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
select poll_private.close_due_polls();
select poll_private.close_due_polls();
do $legacy_notice$
declare v_notices int; v_receipts int;
begin
 select count(*) into v_notices from public.notifications
  where type='poll_closed' and post_id='20000000-0000-0000-0000-000000000098';
 select count(*) into v_receipts from poll_private.close_receipts
  where post_id='20000000-0000-0000-0000-000000000098';
 if v_notices<>1 or v_receipts<>0 then
  raise exception 'Legacy notification replay: notifications %, receipts %',v_notices,v_receipts;
 end if;
end
$legacy_notice$;
SQL
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
# The old cron has been removed but an invocation may remain in run history.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
insert into cron.job_run_details(runid,jobid,command,status,username,database)
values(987654321,987654321,'select public.dispatch_poll_closed_notifications();','running','postgres','postgres');
SQL
if docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/schedule_candidate.sql > docs/qa/issue22-polls-20261020/cron-inflight-guard.log 2>&1; then
  echo "FAIL: scheduler accepted an in-flight poll close execution" >&2
  exit 1
fi
grep -q 'Previous interactive cron execution still running; wait for drain' docs/qa/issue22-polls-20261020/cron-inflight-guard.log
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
delete from cron.job_run_details where runid=987654321 and jobid=987654321
  and command='select public.dispatch_poll_closed_notifications();';
SQL
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/schedule_candidate.sql
"${qa_compose[@]}" up -d --wait rest
python tests/polls/verify_isolated.py
# Verify synthetic fixture backup can be restored separately without writing to production.
bash tests/polls/verify_backup_restore.sh
# Regression: emergency disable must unschedule a still-present legacy cron.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
select cron.schedule('poker_id_poll_closed_notifications','* * * * *','select public.dispatch_poll_closed_notifications();');
SQL
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
 if exists(select 1 from cron.job where jobname='poker_id_poll_closed_notifications') then raise exception 'Rollback retained legacy scheduler'; end if;
 if to_regclass('poll_private.close_receipts') is null then raise exception 'Rollback removed private close receipts'; end if;
 if has_schema_privilege('authenticated','poll_private','USAGE') then raise exception 'Rollback retained private schema usage'; end if;
 if exists (
  select 1 from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
  where ns.nspname='poll_private'
    and (has_function_privilege('authenticated',p.oid,'EXECUTE')
      or has_function_privilege('anon',p.oid,'EXECUTE'))
 ) then raise exception 'Rollback retained private poll function execution rights'; end if;

 if not exists(select 1 from pg_policies where schemaname='public' and tablename='notifications' and policyname='poll_closed_forgery_guard_v1') then raise exception 'Rollback removed notification guard'; end if;
 if exists(select 1 from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace where ns.nspname='public' and p.proname in ('get_interactive_results_v2','get_interactive_results_v3') and has_function_privilege('authenticated',p.oid,'EXECUTE')) then raise exception 'Rollback exposed historical results RPC'; end if;
end
$rollback_check$;
SQL
# Prove a safe re-enable cycle in the disposable database after a
# fail-closed disable: do NOT replay legacy notifications or lose history.
for reactivate_pass in 1 2; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/core_without_notifications_candidate.sql
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/forward_candidate.sql
done
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $reactivation_check$
declare r record; n int;
begin
 if not has_schema_privilege('authenticated','poll_private','USAGE') then raise exception 'Reactivation did not restore private schema usage'; end if;
 for r in select p.oid, p.proname from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
 where ns.nspname='poll_private' and p.proname in ('create_poll','submit_vote','legacy_vote','poll_results') loop
  if not has_function_privilege('authenticated',r.oid,'EXECUTE') then raise exception 'Reactivation did not restore helper %',r.proname; end if;
  if has_function_privilege('anon',r.oid,'EXECUTE') then raise exception 'Reactivation exposed helper % to anon',r.proname; end if;
 end loop;
 if (select count(*) from pg_proc p join pg_namespace ns on ns.oid=p.pronamespace
      where ns.nspname='poll_private' and p.proname in ('create_poll','submit_vote','legacy_vote','poll_results')) <> 4 then
  raise exception 'Reactivation lost a required helper'; end if;
 if not has_function_privilege('authenticated','public.create_interactive_post_v4(text,text,text[],integer,boolean,text)','EXECUTE') then raise exception 'Creation RPC not restored'; end if;
 if not has_function_privilege('authenticated','public.get_interactive_results_v4(uuid[])','EXECUTE') then raise exception 'Result RPC not restored'; end if;
 if has_function_privilege('authenticated','public.get_interactive_results_v3(uuid[])','EXECUTE') then raise exception 'Old result RPC exposed'; end if;
 if has_function_privilege('authenticated','poll_private.close_due_polls()','EXECUTE') then raise exception 'Private close worker unexpectedly exposed'; end if;
 -- RLS and direct DML controls must survive disable + repeated re-enable.
 if not (select relrowsecurity from pg_class where oid='public.post_interactive_responses'::regclass) then raise exception 'Vote RLS disabled'; end if;
 if not (select relrowsecurity from pg_class where oid='public.post_interactive'::regclass) then raise exception 'Poll metadata RLS disabled'; end if;
 if not (select relrowsecurity from pg_class where oid='public.notifications'::regclass) then raise exception 'Notification RLS disabled'; end if;
 if (select count(*) from pg_policies where schemaname='public' and tablename='post_interactive_responses' and policyname='poll_raw_identity_guard_v1' and permissive='RESTRICTIVE' and cmd='SELECT' and replace(qual,' ','')='false') <> 1 then
  raise exception 'Anonymous voter raw identity protection not restored'; end if;
 if not exists(select 1 from pg_policies where schemaname='public' and tablename='post_interactive' and policyname='poll_metadata_visibility_v1' and permissive='RESTRICTIVE' and cmd='SELECT') then raise exception 'Poll metadata visibility guard not restored'; end if;
 if not exists(select 1 from pg_policies where schemaname='public' and tablename='notifications' and policyname='poll_closed_forgery_guard_v1' and permissive='RESTRICTIVE' and cmd='INSERT') then raise exception 'Forged closed-notice policy not restored'; end if;
 if not exists(select 1 from pg_trigger where tgname='poll_closed_guard_v1' and tgrelid='public.notifications'::regclass and not tgisinternal and tgenabled <> 'D') then raise exception 'Closed-notification immutability trigger not restored'; end if;
 for r in select unnest(array['public.post_interactive','public.post_interactive_responses'])::regclass as rel loop
  if has_table_privilege('authenticated',r.rel,'INSERT') or has_table_privilege('authenticated',r.rel,'UPDATE') or has_table_privilege('authenticated',r.rel,'DELETE') then raise exception 'Poll raw table DML grant exposed: %',r.rel; end if;
 end loop;
 if has_function_privilege('anon','public.get_interactive_results_v4(uuid[])','EXECUTE') then raise exception 'Anonymous results RPC exposed'; end if;
 if has_function_privilege('authenticated','public.get_interactive_results_v2(uuid[])','EXECUTE') then raise exception 'Legacy v2 result exposed'; end if;
 if has_function_privilege('authenticated','public.finish_due_polls_v1()','EXECUTE') then raise exception 'Close RPC exposed'; end if;
 if has_function_privilege('authenticated','poll_private.guard_closed_notification()','EXECUTE') then raise exception 'Notice trigger helper exposed'; end if;
 select count(*) into n from public.post_interactive where post_id='20000000-0000-0000-0000-000000000001' and kind='question';
 if n <> 1 then raise exception 'Reactivation lost historical question'; end if;
 select count(*) into n from public.post_interactive_responses where post_id='20000000-0000-0000-0000-000000000001' and answer='historical answer fixture';
 if n <> 1 then raise exception 'Reactivation lost historical answer'; end if;
 select count(*) into n from public.notifications where type='poll_closed' and post_id='20000000-0000-0000-0000-000000000098';
 if n <> 1 then raise exception 'Reactivation replayed legacy close notice'; end if;
 if exists(select 1 from cron.job where jobname='pokerid-poll-close-v1') then raise exception 'Reactivation started cron without separate owner action'; end if;
end
$reactivation_check$;
SQL
echo 'PASS poll reactivation cycle: grants restored, historical rows preserved, no cron auto-start'


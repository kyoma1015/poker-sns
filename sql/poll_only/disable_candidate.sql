-- Fail-closed feature-disable rollback: retain ALL posts, votes, private close
-- receipts, original question data, privacy policies and notification guards.
-- This is deliberately NOT an unsafe full schema/grant restoration.
begin;
do $$
declare r record;
begin
 if to_regclass('cron.job') is not null then
  perform cron.unschedule(jobid) from cron.job where jobname='pokerid-poll-close-v1';
 end if;
 for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('create_interactive_post','create_interactive_post_v2','create_interactive_post_v3','create_interactive_post_v4','submit_interactive_response','submit_interactive_response_v2','get_interactive_results','get_interactive_results_v2','get_interactive_results_v3','get_interactive_results_v4','finish_due_polls_v1') loop
 execute format('revoke execute on function %s from public,anon,authenticated',r.sig);
 end loop;
end $$;
-- Also deny direct access to poll_private helpers if that schema is ever
-- included in exposed schemas. Preserve the worker's owner/cron execution
-- permissions and preserve all existing user data, RLS and triggers.
do $private_disable$
declare r record;
begin
 if to_regnamespace('poll_private') is not null then
  revoke usage on schema poll_private from public,anon,authenticated;
  for r in select p.oid::regprocedure sig
    from pg_proc p join pg_namespace n on n.oid=p.pronamespace
    where n.nspname='poll_private'
  loop
   execute format('revoke execute on function %s from public,anon,authenticated',r.sig);
  end loop;
 end if;
end
$private_disable$;
notify pgrst, 'reload schema';
commit;

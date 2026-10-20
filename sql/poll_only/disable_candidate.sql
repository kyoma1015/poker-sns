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
 where n.nspname='public' and p.proname in ('create_interactive_post','create_interactive_post_v2','create_interactive_post_v3','create_interactive_post_v4','submit_interactive_response','submit_interactive_response_v2','get_interactive_results','get_interactive_results_v4','finish_due_polls_v1') loop
 execute format('revoke execute on function %s from public,anon,authenticated',r.sig);
 end loop;
end $$;
notify pgrst, 'reload schema';
commit;

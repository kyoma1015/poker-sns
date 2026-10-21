-- Owner-only isolated QA / reviewed deployment step. pg_cron is required.
-- Production currently has poker_id_poll_closed_notifications calling
-- public.dispatch_poll_closed_notifications() every minute. Do NOT install a
-- second scheduler until its behavior and idempotency have been audited.
-- This script deliberately fails closed while that job exists.
begin;
create extension if not exists pg_cron;
do $$begin
 if exists(select 1 from cron.job where jobname<>'pokerid-poll-close-v1' and command ~* '(poll|interactive)') then
  raise exception 'Existing interactive cron requires review; do not install a second close scheduler';
 end if;
end$$;
select cron.unschedule(jobid) from cron.job where jobname='pokerid-poll-close-v1';
select cron.schedule('pokerid-poll-close-v1','* * * * *','select poll_private.close_due_polls();');
commit;

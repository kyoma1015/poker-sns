-- Disposable QA database ONLY. Synthetic rows, never production data.
-- Mirror verified 2026-10-22 live catalog deltas after the unknown-privacy
-- fail-closed test has completed, before applying poll core.
alter table public.post_interactive
  add column if not exists is_anonymous boolean not null default true,
  add column if not exists question_response_policy text;
alter table public.post_interactive_responses
  add column if not exists is_anonymous boolean;
alter table public.post_interactive
  add constraint question_response_policy_valid
  check (question_response_policy is null or question_response_policy in ('anonymous_only','named_only','respondent_choice'));
drop policy if exists legacy_response_read_fixture on public.post_interactive_responses;
drop policy if exists interactive_responses_own_read on public.post_interactive_responses;
create policy interactive_responses_own_read on public.post_interactive_responses
  for select to authenticated using(user_id=(select auth.uid()));
drop policy if exists legacy_notification_insert on public.notifications;
create policy "Users can create notifications" on public.notifications
  for insert to authenticated with check(auth.uid()=actor_id and auth.uid()<>user_id);
-- Live legacy cron dispatcher body, recreated only in this synthetic DB.
create or replace function public.dispatch_poll_closed_notifications()
returns integer language plpgsql security definer set search_path='' as $$
declare inserted_count integer;
begin
 insert into public.notifications(user_id,actor_id,type,post_id)
 select p.user_id,p.user_id,'poll_closed',pi.post_id
 from public.post_interactive pi join public.posts p on p.id=pi.post_id
 where pi.kind='poll' and pi.closes_at is not null and pi.closes_at<=now()
 and not exists(select 1 from public.notifications n where n.post_id=pi.post_id and n.user_id=p.user_id and n.type='poll_closed')
 on conflict do nothing;
 get diagnostics inserted_count=row_count;
 return inserted_count;
end;$$;
revoke all on function public.dispatch_poll_closed_notifications() from public,anon,authenticated;
-- Assert historical synthetic question/answer rows survive the schema overlay.
do $$begin
 if (select count(*) from public.post_interactive where kind='question')<>1
 or (select count(*) from public.post_interactive_responses where answer='historical answer fixture')<>1 then
  raise exception 'Production parity overlay altered historical fixture';
 end if;
end$$;

-- Return-contract fixtures only: synthetic bodies, NOT copies of live behavior.
-- These endpoints must exist before core so CREATE OR REPLACE is exercised
-- against their observed signatures. No requests run until core replaces them.
create or replace function public.submit_interactive_response_v2(
 p_post_id uuid,p_option_index integer default null,p_answer text default null,p_is_anonymous boolean default false)
returns void language plpgsql security invoker set search_path='' as $fixture_vote$
begin
 raise exception 'Synthetic contract fixture must be replaced before use';
end $fixture_vote$;
create or replace function public.get_interactive_results_v4(p_post_ids uuid[])
returns table(post_id uuid,total_votes bigint,vote_counts jsonb,answers jsonb,my_option_index integer,has_responded boolean,voters jsonb)
language plpgsql stable security invoker set search_path='' as $fixture_results$
begin
 raise exception 'Synthetic contract fixture must be replaced before use';
end $fixture_results$;
revoke all on function public.submit_interactive_response_v2(uuid,integer,text,boolean),public.get_interactive_results_v4(uuid[]) from public,anon,authenticated;

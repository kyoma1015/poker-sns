-- Synthetic isolated QA only: exact return signatures observed in live Supabase.
-- Run before and after core migration to catch CREATE OR REPLACE return-type
-- incompatibilities. No production data, secrets or writes.
do $$
declare v_actual text; v_expected text;
begin
 for v_actual,v_expected in
  select pg_get_function_result(to_regprocedure('public.create_interactive_post_v3(text,text,text[],integer,boolean)')), 'uuid'
  union all select pg_get_function_result(to_regprocedure('public.submit_interactive_response_v2(uuid,integer,text,boolean)')), 'void'
  union all select pg_get_function_result(to_regprocedure('public.get_interactive_results_v4(uuid[])')),
    'TABLE(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean, voters jsonb)'
  union all select pg_get_function_result(to_regprocedure('public.get_interactive_results_v3(uuid[])')),
    'TABLE(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean, voters jsonb)'
  union all select pg_get_function_result(to_regprocedure('public.get_interactive_results_v2(uuid[])')),
    'TABLE(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean)'
 loop
  if v_actual is distinct from v_expected then
   raise exception 'Live RPC return signature mismatch: got %, expected %',v_actual,v_expected;
  end if;
 end loop;
 if to_regprocedure('public.dispatch_poll_closed_notifications()') is null
    or pg_get_function_result('public.dispatch_poll_closed_notifications()'::regprocedure)<>'integer' then
  raise exception 'Existing legacy close dispatcher signature changed';
 end if;
 if not exists(select 1 from pg_policies where schemaname='public'
    and tablename='post_interactive_responses' and policyname='interactive_responses_own_read') then
  raise exception 'Production legacy respondent RLS missing';
 end if;
end $$;

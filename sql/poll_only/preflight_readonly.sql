-- Run only on an explicitly authorized isolated/staging DB. Never fetch a
-- production password to execute this task. No user-row data or secret values.
select c.relname,c.relrowsecurity,a.attname,format_type(a.atttypid,a.atttypmod) type,a.attnotnull,pg_get_expr(d.adbin,d.adrelid) default_expression
from pg_class c join pg_namespace n on n.oid=c.relnamespace join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped left join pg_attrdef d on d.adrelid=c.oid and d.adnum=a.attnum
where n.nspname='public' and c.relname in ('posts','profiles','user_blocks','notifications','post_interactive','post_interactive_responses') order by c.relname,a.attnum;
select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where schemaname='public' and tablename in ('posts','profiles','user_blocks','notifications','post_interactive','post_interactive_responses');
select p.oid::regprocedure signature,p.prosecdef,p.proacl,md5(pg_get_functiondef(p.oid)) definition_hash from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname ~ '(interactive|poll)';
select table_name,grantee,privilege_type from information_schema.role_table_grants where table_schema='public' and table_name in ('notifications','post_interactive','post_interactive_responses');

-- Read-only release gates. An operator must re-run immediately before
-- approved deployment: counts are a time-sensitive snapshot, not a lock.
select kind,count(*) rows from public.post_interactive group by kind order by kind;
select count(*) responses,
 count(*) filter(where option_index is not null) poll_votes,
 count(*) filter(where answer is not null) question_answers
from public.post_interactive_responses;
select count(*) poll_closed_notifications from public.notifications where type='poll_closed';
select count(*) duplicate_closed_notice_pairs from (
 select post_id,user_id from public.notifications
 where type='poll_closed' and post_id is not null
 group by post_id,user_id having count(*)>1
) duplicate_pairs;
select count(*) closed_polls_missing_owner_notification
from public.post_interactive i join public.posts p on p.id=i.post_id
where i.kind='poll' and i.closes_at<=now()
and not exists(
 select 1 from public.notifications n
 where n.post_id=i.post_id and n.user_id=p.user_id and n.type='poll_closed'
);
select jobid,jobname,schedule,active,command
from cron.job where command ~* '(poll|interactive)' order by jobid;
select status,count(*) total,max(start_time) latest_start,max(end_time) latest_end
from cron.job_run_details
where jobid in(select jobid from cron.job where command ~* '(poll|interactive)')
group by status order by status;
select count(*) currently_running
from cron.job_run_details
where jobid in(select jobid from cron.job where command ~* '(poll|interactive)')
and status='running';
select n.nspname||'.'||p.proname as function_name,
 oidvectortypes(p.proargtypes) args,pg_get_function_result(p.oid) return_type,
 p.prosecdef as security_definer
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where (n.nspname='public' and (p.proname like '%interactive%' or p.proname like '%poll%'))
or n.nspname='poll_private'
order by function_name,args;

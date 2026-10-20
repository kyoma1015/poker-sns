-- Run only on an explicitly authorized isolated/staging DB. Never fetch a
-- production password to execute this task. No user-row data or secret values.
select c.relname,c.relrowsecurity,a.attname,format_type(a.atttypid,a.atttypmod) type,a.attnotnull,pg_get_expr(d.adbin,d.adrelid) default_expression
from pg_class c join pg_namespace n on n.oid=c.relnamespace join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped left join pg_attrdef d on d.adrelid=c.oid and d.adnum=a.attnum
where n.nspname='public' and c.relname in ('posts','profiles','user_blocks','notifications','post_interactive','post_interactive_responses') order by c.relname,a.attnum;
select schemaname,tablename,policyname,permissive,roles,cmd,qual,with_check from pg_policies where schemaname='public' and tablename in ('posts','profiles','user_blocks','notifications','post_interactive','post_interactive_responses');
select p.oid::regprocedure signature,p.prosecdef,p.proacl,md5(pg_get_functiondef(p.oid)) definition_hash from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname ~ '(interactive|poll)';
select table_name,grantee,privilege_type from information_schema.role_table_grants where table_schema='public' and table_name in ('notifications','post_interactive','post_interactive_responses');

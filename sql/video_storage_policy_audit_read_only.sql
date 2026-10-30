-- READ-ONLY SECURITY AUDIT. REVIEW BEFORE APPLYING TO ANY ENVIRONMENT.
-- Queries only; no DDL, DML, privilege changes or production writes.
-- Run using a trusted SQL console and inspect ALL returned policies.
select
  p.schemaname,
  p.tablename,
  p.policyname,
  p.permissive,
  p.roles,
  p.cmd,
  p.qual,
  p.with_check
from pg_policies p
where p.schemaname = 'storage'
  and p.tablename = 'objects'
order by p.cmd, p.policyname;

-- Permissive policies combine with OR. Even policies named for other
-- buckets must be inspected for predicates that can match post-videos.
select
  b.id, b.public, b.file_size_limit, b.allowed_mime_types
from storage.buckets b
where b.id = 'post-videos';

-- Object UPDATE/DELETE grants may bypass expected owner-only behavior
-- through other roles or SECURITY DEFINER functions. Manual review required.
select grantee, privilege_type, is_grantable
from information_schema.role_table_grants
where table_schema = 'storage' and table_name = 'objects'
order by grantee, privilege_type;

-- This report is NOT an immutability proof. Also inspect Storage service
-- roles, object overwrite API behavior, triggers and privileged workers.

-- Privileged writer inventory: BYPASSRLS and table owners may bypass policies.
-- Any role with direct Storage object writes needs a separate authorization
-- and API-path review. This is read-only and does not approve production use.
select r.rolname, r.rolsuper, r.rolbypassrls, r.rolcanlogin,
       has_table_privilege(r.oid,'storage.objects','INSERT') as can_insert,
       has_table_privilege(r.oid,'storage.objects','UPDATE') as can_update,
       has_table_privilege(r.oid,'storage.objects','DELETE') as can_delete
from pg_roles r
where has_table_privilege(r.oid,'storage.objects','INSERT')
   or has_table_privilege(r.oid,'storage.objects','UPDATE')
   or has_table_privilege(r.oid,'storage.objects','DELETE')
order by r.rolbypassrls desc,r.rolname;

-- Identify SECURITY DEFINER routines that could modify Storage objects
-- without respecting authenticated client RLS. Source inspection is required
-- for each returned routine, including dynamic SQL and nested calls.
select n.nspname as schema_name,p.proname as function_name,
       pg_get_function_identity_arguments(p.oid) as arguments,
       pg_get_userbyid(p.proowner) as owner_name,
       p.prosecdef as security_definer,
       pg_get_functiondef(p.oid) as definition
from pg_proc p join pg_namespace n on n.oid=p.pronamespace
where p.prosecdef
  and (pg_get_functiondef(p.oid) ilike '%storage.objects%'
       or pg_get_functiondef(p.oid) ilike '%post-videos%')
order by n.nspname,p.proname;

-- Trigger-based writes and privileged functions are part of the writer
-- inventory. A clean result here still does not cover Storage service APIs.
select t.tgname, t.tgenabled, pg_get_triggerdef(t.oid) as definition
from pg_trigger t
where t.tgrelid='storage.objects'::regclass and not t.tgisinternal
order by t.tgname;

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

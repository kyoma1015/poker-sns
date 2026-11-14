-- REVIEW ONLY / NEVER APPLY TO PRODUCTION WITHOUT SEPARATE APPROVAL.
-- Supabase PostgreSQL permissive INSERT policies combine with OR.
-- This additive RESTRICTIVE policy makes the video bucket obey the DB
-- publication gate even when an older permissive INSERT policy accepts
-- owner + reservation without checking video_rollout_allowed().
-- Other buckets are unaffected. This file is deliberately NOT executed by CI.
-- Before applying: review existing roles, storage.objects RLS, policy OR/AND
-- composition and real JWT access in a production-schema isolated project.
begin;
do $preflight$
begin
 if to_regclass('storage.objects') is null
    or to_regprocedure('public.video_rollout_allowed()') is null
 then raise exception 'video insert stop preflight: dependency missing'; end if;
 if not exists (select 1 from pg_class where oid='storage.objects'::regclass and relrowsecurity)
 then raise exception 'video insert stop preflight: storage RLS disabled'; end if;
 if exists(select 1 from pg_policies where schemaname='storage' and tablename='objects'
           and policyname='video_recovery_restrict_video_bucket_insert')
 then
   if not exists(select 1 from pg_policies
     where schemaname='storage' and tablename='objects'
       and policyname='video_recovery_restrict_video_bucket_insert'
       and cmd='INSERT' and permissive='RESTRICTIVE'
       and roles @> array['authenticated']::name[]
       and with_check='((bucket_id <> ''post-videos''::text) OR video_rollout_allowed())')
   then raise exception 'video insert stop preflight: existing policy differs'; end if;
 else
   create policy video_recovery_restrict_video_bucket_insert
     on storage.objects as restrictive for insert to authenticated
     with check (bucket_id <> 'post-videos' or public.video_rollout_allowed());
 end if;
end $preflight$;
commit;

-- ROLLBACK (only with separate approval, in a maintenance window):
-- DROP POLICY IF EXISTS video_recovery_restrict_video_bucket_insert ON storage.objects;
-- Do NOT execute rollback automatically: removing a restrictive policy can
-- re-enable INSERT via OR-combined permissive policies, including during a stop.

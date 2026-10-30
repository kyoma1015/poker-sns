-- REVIEW ONLY. Applied exclusively to disposable isolated CI, never production.
-- Atomic DDL avoids a window where newly created SECURITY DEFINER functions
-- have PostgreSQL's default PUBLIC EXECUTE before their REVOKE statements.
begin;
-- CANDIDATE ONLY: NOT APPROVED FOR PRODUCTION EXECUTION.
-- Preflight stops if existing public video infrastructure differs from the audited baseline.
-- SQL must be independently reviewed, tested against a production-like isolated project,
-- and explicitly approved before any application. No automatic deployment.
do $preflight$
declare fn text;
begin
  if to_regclass('public.video_reserved_object_keys') is null
     or to_regclass('public.posts') is null
     or to_regclass('storage.objects') is null
     or to_regclass('auth.sessions') is null
     or to_regclass('video_private.consumed_nonces') is null
     or to_regclass('video_private.general_public_rollout') is null
  then raise exception 'video recovery preflight: baseline schema missing'; end if;
  if not exists (select 1 from pg_class c where c.oid='public.video_reserved_object_keys'::regclass and c.relrowsecurity)
     or not exists (select 1 from pg_class c where c.oid='public.posts'::regclass and c.relrowsecurity)
  then raise exception 'video recovery preflight: required RLS disabled'; end if;
  if to_regprocedure('public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)') is null
     or to_regprocedure('public.video_reserve_object_key(uuid,text)') is null
     or to_regprocedure('public.video_rollout_allowed()') is null
  then raise exception 'video recovery preflight: baseline RPC missing'; end if;
  if not has_function_privilege('authenticated','public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)','EXECUTE')
    or has_function_privilege('anon','public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)','EXECUTE')
  then raise exception 'video recovery preflight: parent publisher grants mismatch'; end if;
  if not exists (select 1 from pg_constraint
       where conrelid='public.video_reserved_object_keys'::regclass and contype in ('p','u')
       and conkey = (select array_agg(attnum order by attnum)::smallint[]
                    from pg_attribute where attrelid='public.video_reserved_object_keys'::regclass
                      and attname in ('bucket_id','object_path') and attnum>0))
  then raise exception 'video recovery preflight: reservation composite key missing'; end if;
  if not exists (select 1 from information_schema.columns
       where table_schema='auth' and table_name='sessions' and column_name='not_after')
  then raise exception 'video recovery preflight: session expiration column missing'; end if;
  -- All-or-none migration seal: repeat execution is allowed ONLY when every
  -- previously installed function still has its exact audited definition.
  -- A partial install or any drift aborts the entire transaction.
  if to_regclass('video_private.recovery_migration_seal') is null then
    if to_regclass('video_private.recovery_manifests') is not null
       or to_regprocedure('public.video_bind_recovery_manifest_v1(text,text,integer,text,text)') is not null
       or to_regprocedure('public.video_recovery_state_v1(text)') is not null
       or to_regprocedure('video_private.assert_recovery_identity(uuid)') is not null
       or to_regprocedure('public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)') is not null
    then raise exception 'video recovery preflight: preexisting unsealed migration objects'; end if;
  else
    if to_regclass('video_private.recovery_manifests') is null
       or to_regprocedure('public.video_bind_recovery_manifest_v1(text,text,integer,text,text)') is null
       or to_regprocedure('public.video_recovery_state_v1(text)') is null
       or to_regprocedure('video_private.assert_recovery_identity(uuid)') is null
       or to_regprocedure('public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)') is null
    then raise exception 'video recovery preflight: incomplete sealed migration'; end if;
    if not exists (
      select 1 from video_private.recovery_migration_seal
      where version='recovery-v1'
        and definition_digest=md5(
           pg_get_functiondef('public.video_bind_recovery_manifest_v1(text,text,integer,text,text)'::regprocedure) ||
           pg_get_functiondef('public.video_recovery_state_v1(text)'::regprocedure) ||
           pg_get_functiondef('video_private.assert_recovery_identity(uuid)'::regprocedure) ||
           pg_get_functiondef('public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)'::regprocedure)
        )
    ) then raise exception 'video recovery preflight: function definition drift or missing migration seal'; end if;
    if not exists (select 1 from pg_class where oid='video_private.recovery_manifests'::regclass and relrowsecurity)
       or has_table_privilege('anon','video_private.recovery_manifests','SELECT')
       or has_table_privilege('authenticated','video_private.recovery_manifests','SELECT')
       or has_function_privilege('anon','public.video_recovery_state_v1(text)','EXECUTE')
       or not has_function_privilege('authenticated','public.video_recovery_state_v1(text)','EXECUTE')
    then raise exception 'video recovery preflight: RLS or grants drift'; end if;
  end if;
end $preflight$;
create schema if not exists video_private;
-- Do not revoke existing schema USAGE: video_private is shared with production
-- video attestation, nonce and rollout machinery. This migration only revokes
-- access to its own new table and functions.
create table if not exists video_private.recovery_manifests (
 object_path text primary key,
 bucket_id text not null default 'post-videos' check(bucket_id='post-videos'),
 foreign key(bucket_id,object_path) references public.video_reserved_object_keys(bucket_id,object_path),
 content text not null check(length(content)<=10000),
 owner_id uuid not null, sha256 text not null check(sha256 ~ '^[0-9a-f]{64}$'),
 size_bytes integer not null check(size_bytes between 1 and 20971520),
 media_type text not null check(media_type in ('video/mp4','video/webm')),
 expires_at timestamptz not null
);
-- Private seal only: never grants app users access or stores sensitive data.
create table if not exists video_private.recovery_migration_seal (
 version text primary key,
 definition_digest text not null check (definition_digest ~ '^[0-9a-f]{32}$')
);
revoke all on video_private.recovery_migration_seal from public,anon,authenticated,service_role;
alter table video_private.recovery_manifests enable row level security;
revoke all on video_private.recovery_manifests from public,anon,authenticated,service_role;

create or replace function public.video_bind_recovery_manifest_v1(p_path text,p_sha256 text,p_size integer,p_type text,p_content text)
returns bigint language plpgsql security definer set search_path='' as $$
declare r public.video_reserved_object_keys%rowtype; m video_private.recovery_manifests%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text or
 p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_size is null or p_size not between 1 and 20971520 or
 p_content is null or length(p_content)>10000 or p_type is null or p_type not in ('video/mp4','video/webm') or
 not ( (p_type='video/mp4' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]mp4$') or
       (p_type='video/webm' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]webm$') )
 then raise exception 'invalid recovery manifest'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path;
 if found then
   if m.owner_id is distinct from v_owner or m.sha256 is distinct from p_sha256 or m.size_bytes is distinct from p_size or m.media_type is distinct from p_type or m.content is distinct from p_content then raise exception 'conflicting recovery manifest'; end if;
   return extract(epoch from m.expires_at)::bigint;
 end if;
 -- Binding existing objects/posts after a restart would let local hints invent
 -- original-file identity. Only a pre-upload manifest is eligible.
 if exists(select 1 from storage.objects where bucket_id='post-videos' and name=p_path) or
 exists(select 1 from public.posts where video_path=p_path) then raise exception 'manifest must precede upload'; end if;
 insert into video_private.recovery_manifests(object_path,owner_id,sha256,size_bytes,media_type,content,expires_at) values(p_path,v_owner,p_sha256,p_size,p_type,p_content,r.created_at+interval '1 hour');
 return extract(epoch from r.created_at+interval '1 hour')::bigint;
end $$;

create or replace function public.video_recovery_state_v1(p_path text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype;
 o storage.objects%rowtype; p public.posts%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text then raise exception 'recovery owner mismatch'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'recovery manifest unavailable'; end if;
 select * into o from storage.objects where bucket_id='post-videos' and name=p_path;
 if o.id is not null and o.owner_id is distinct from v_owner::text then raise exception 'Storage owner mismatch'; end if;
 select * into p from public.posts where video_path=p_path;
 if p.id is not null and p.user_id is distinct from v_owner then raise exception 'post owner mismatch'; end if;
 return jsonb_build_object('owner',v_owner,'path',p_path,'sha256',m.sha256,'size',m.size_bytes,'type',m.media_type,
 'content',m.content,'expires',extract(epoch from m.expires_at)::bigint,
 'active',m.expires_at>clock_timestamp() and r.created_at+interval '1 hour'>clock_timestamp(),
 'generation',o.id,'post_id',p.id,'post_generation',p.video_generation,'post_sha256',p.video_sha256,'post_duration',p.video_duration_seconds);
end $$;
revoke all on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) from public,anon,service_role;
revoke all on function public.video_recovery_state_v1(text) from public,anon,service_role;
grant execute on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) to authenticated;
grant execute on function public.video_recovery_state_v1(text) to authenticated;

-- Private, volatile check: PostgREST validates JWTs at request admission, but
-- a reservation/Storage lock wait can cross expiry or a session revocation.
-- Lock the exact Auth session AFTER reservation acquisition so revocation
-- during that wait is observable; key-share fences deletion until commit.
create or replace function video_private.assert_recovery_identity(p_owner uuid)
returns void language plpgsql volatile security definer set search_path='' as $$
declare v_exp text := auth.jwt()->>'exp'; v_session text := auth.jwt()->>'session_id';
begin
 if p_owner is null or auth.uid() is distinct from p_owner or
 v_exp is null or v_exp !~ '^[0-9]{1,12}$' or
 v_session is null or v_session !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
 then raise exception 'recovery identity unavailable'; end if;
 if v_exp::numeric <= extract(epoch from clock_timestamp()) then raise exception 'recovery JWT expired'; end if;
 perform 1 from auth.sessions where id=v_session::uuid and user_id=p_owner
 and (not_after is null or not_after>clock_timestamp()) for key share;
 if not found then raise exception 'recovery session unavailable'; end if;
 -- The session lookup itself can wait on Auth, so re-evaluate the clock.
 if auth.uid() is distinct from p_owner or v_exp::numeric <= extract(epoch from clock_timestamp())
 then raise exception 'recovery JWT expired'; end if;
end $$;
revoke all on function video_private.assert_recovery_identity(uuid) from public,anon,authenticated,service_role;

-- Recovery-specific atomic publication fence. A read-only status result is
-- never authority: recheck owner, expiry and original hash in the transaction
-- that validates HMAC/generation/nonce and inserts/reconciles the post.
create or replace function public.video_publish_recovered_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype; v_id uuid;
begin
 if p_owner is null or (select auth.uid()) is distinct from p_owner then raise exception 'recovery owner mismatch'; end if;
 -- Match parent publish's reservation-before-Storage lock order.
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'recovery reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=p_owner for update;
 if not found or m.expires_at<=clock_timestamp() or m.sha256 is distinct from p_sha256 or m.content is distinct from p_content then raise exception 'recovery manifest mismatch or expired'; end if;
 perform video_private.assert_recovery_identity(p_owner);
 v_id:=public.video_publish_attested_v1(p_owner,p_path,p_generation,p_sha256,p_duration_ms,p_content,p_expires_at,p_nonce,p_signature,p_key_id);
 -- A lock wait inside parent publication must not outlive auth or either deadline.
 perform video_private.assert_recovery_identity(p_owner);
 if m.expires_at<=clock_timestamp() or r.created_at+interval '1 hour'<=clock_timestamp() or
 p_expires_at<=extract(epoch from clock_timestamp())::bigint then raise exception 'recovery expired during publication'; end if;
 return v_id;
end $$;
revoke all on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,service_role;
grant execute on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;

commit;
)
);
revoke all on video_private.recovery_migration_seal from public,anon,authenticated,service_role;
alter table video_private.recovery_manifests enable row level security;
revoke all on video_private.recovery_manifests from public,anon,authenticated,service_role;

create or replace function public.video_bind_recovery_manifest_v1(p_path text,p_sha256 text,p_size integer,p_type text,p_content text)
returns bigint language plpgsql security definer set search_path='' as $$
declare r public.video_reserved_object_keys%rowtype; m video_private.recovery_manifests%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text or
 p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_size is null or p_size not between 1 and 20971520 or
 p_content is null or length(p_content)>10000 or p_type is null or p_type not in ('video/mp4','video/webm') or
 not ( (p_type='video/mp4' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]mp4$') or
       (p_type='video/webm' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]webm$') )
 then raise exception 'invalid recovery manifest'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path;
 if found then
   if m.owner_id is distinct from v_owner or m.sha256 is distinct from p_sha256 or m.size_bytes is distinct from p_size or m.media_type is distinct from p_type or m.content is distinct from p_content then raise exception 'conflicting recovery manifest'; end if;
   return extract(epoch from m.expires_at)::bigint;
 end if;
 -- Binding existing objects/posts after a restart would let local hints invent
 -- original-file identity. Only a pre-upload manifest is eligible.
 if exists(select 1 from storage.objects where bucket_id='post-videos' and name=p_path) or
 exists(select 1 from public.posts where video_path=p_path) then raise exception 'manifest must precede upload'; end if;
 insert into video_private.recovery_manifests(object_path,owner_id,sha256,size_bytes,media_type,content,expires_at) values(p_path,v_owner,p_sha256,p_size,p_type,p_content,r.created_at+interval '1 hour');
 return extract(epoch from r.created_at+interval '1 hour')::bigint;
end $$;

create or replace function public.video_recovery_state_v1(p_path text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype;
 o storage.objects%rowtype; p public.posts%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text then raise exception 'recovery owner mismatch'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'recovery manifest unavailable'; end if;
 select * into o from storage.objects where bucket_id='post-videos' and name=p_path;
 if o.id is not null and o.owner_id is distinct from v_owner::text then raise exception 'Storage owner mismatch'; end if;
 select * into p from public.posts where video_path=p_path;
 if p.id is not null and p.user_id is distinct from v_owner then raise exception 'post owner mismatch'; end if;
 return jsonb_build_object('owner',v_owner,'path',p_path,'sha256',m.sha256,'size',m.size_bytes,'type',m.media_type,
 'content',m.content,'expires',extract(epoch from m.expires_at)::bigint,
 'active',m.expires_at>clock_timestamp() and r.created_at+interval '1 hour'>clock_timestamp(),
 'generation',o.id,'post_id',p.id,'post_generation',p.video_generation,'post_sha256',p.video_sha256,'post_duration',p.video_duration_seconds);
end $$;
revoke all on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) from public,anon,service_role;
revoke all on function public.video_recovery_state_v1(text) from public,anon,service_role;
grant execute on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) to authenticated;
grant execute on function public.video_recovery_state_v1(text) to authenticated;

-- Private, volatile check: PostgREST validates JWTs at request admission, but
-- a reservation/Storage lock wait can cross expiry or a session revocation.
-- Lock the exact Auth session AFTER reservation acquisition so revocation
-- during that wait is observable; key-share fences deletion until commit.
create or replace function video_private.assert_recovery_identity(p_owner uuid)
returns void language plpgsql volatile security definer set search_path='' as $$
declare v_exp text := auth.jwt()->>'exp'; v_session text := auth.jwt()->>'session_id';
begin
 if p_owner is null or auth.uid() is distinct from p_owner or
 v_exp is null or v_exp !~ '^[0-9]{1,12}$' or
 v_session is null or v_session !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
 then raise exception 'recovery identity unavailable'; end if;
 if v_exp::numeric <= extract(epoch from clock_timestamp()) then raise exception 'recovery JWT expired'; end if;
 perform 1 from auth.sessions where id=v_session::uuid and user_id=p_owner
 and (not_after is null or not_after>clock_timestamp()) for key share;
 if not found then raise exception 'recovery session unavailable'; end if;
 -- The session lookup itself can wait on Auth, so re-evaluate the clock.
 if auth.uid() is distinct from p_owner or v_exp::numeric <= extract(epoch from clock_timestamp())
 then raise exception 'recovery JWT expired'; end if;
end $$;
revoke all on function video_private.assert_recovery_identity(uuid) from public,anon,authenticated,service_role;

-- Recovery-specific atomic publication fence. A read-only status result is
-- never authority: recheck owner, expiry and original hash in the transaction
-- that validates HMAC/generation/nonce and inserts/reconciles the post.
create or replace function public.video_publish_recovered_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype; v_id uuid;
begin
 if p_owner is null or (select auth.uid()) is distinct from p_owner then raise exception 'recovery owner mismatch'; end if;
 -- Match parent publish's reservation-before-Storage lock order.
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'recovery reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=p_owner for update;
 if not found or m.expires_at<=clock_timestamp() or m.sha256 is distinct from p_sha256 or m.content is distinct from p_content then raise exception 'recovery manifest mismatch or expired'; end if;
 perform video_private.assert_recovery_identity(p_owner);
 v_id:=public.video_publish_attested_v1(p_owner,p_path,p_generation,p_sha256,p_duration_ms,p_content,p_expires_at,p_nonce,p_signature,p_key_id);
 -- A lock wait inside parent publication must not outlive auth or either deadline.
 perform video_private.assert_recovery_identity(p_owner);
 if m.expires_at<=clock_timestamp() or r.created_at+interval '1 hour'<=clock_timestamp() or
 p_expires_at<=extract(epoch from clock_timestamp())::bigint then raise exception 'recovery expired during publication'; end if;
 return v_id;
end $$;
revoke all on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,service_role;
grant execute on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;

-- Seal the exact SQL function definitions after first install. Identical reapply
-- is safe, while a future human/manual edit requires explicit review.
insert into video_private.recovery_migration_seal(version,definition_digest)
values ('recovery-v1',md5(
  pg_get_functiondef('public.video_bind_recovery_manifest_v1(text,text,integer,text,text)'::regprocedure) ||
  pg_get_functiondef('public.video_recovery_state_v1(text)'::regprocedure) ||
  pg_get_functiondef('video_private.assert_recovery_identity(uuid)'::regprocedure) ||
  pg_get_functiondef('public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)'::regprocedure)
))
on conflict (version) do nothing;

commit;
)
revoke all on video_private.recovery_manifests from public,anon,authenticated,service_role;

create or replace function public.video_bind_recovery_manifest_v1(p_path text,p_sha256 text,p_size integer,p_type text,p_content text)
returns bigint language plpgsql security definer set search_path='' as $$
declare r public.video_reserved_object_keys%rowtype; m video_private.recovery_manifests%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text or
 p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_size is null or p_size not between 1 and 20971520 or
 p_content is null or length(p_content)>10000 or p_type is null or p_type not in ('video/mp4','video/webm') or
 not ( (p_type='video/mp4' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]mp4$') or
       (p_type='video/webm' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]webm$') )
 then raise exception 'invalid recovery manifest'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path;
 if found then
   if m.owner_id is distinct from v_owner or m.sha256 is distinct from p_sha256 or m.size_bytes is distinct from p_size or m.media_type is distinct from p_type or m.content is distinct from p_content then raise exception 'conflicting recovery manifest'; end if;
   return extract(epoch from m.expires_at)::bigint;
 end if;
 -- Binding existing objects/posts after a restart would let local hints invent
 -- original-file identity. Only a pre-upload manifest is eligible.
 if exists(select 1 from storage.objects where bucket_id='post-videos' and name=p_path) or
 exists(select 1 from public.posts where video_path=p_path) then raise exception 'manifest must precede upload'; end if;
 insert into video_private.recovery_manifests(object_path,owner_id,sha256,size_bytes,media_type,content,expires_at) values(p_path,v_owner,p_sha256,p_size,p_type,p_content,r.created_at+interval '1 hour');
 return extract(epoch from r.created_at+interval '1 hour')::bigint;
end $$;

create or replace function public.video_recovery_state_v1(p_path text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype;
 o storage.objects%rowtype; p public.posts%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text then raise exception 'recovery owner mismatch'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'recovery manifest unavailable'; end if;
 select * into o from storage.objects where bucket_id='post-videos' and name=p_path;
 if o.id is not null and o.owner_id is distinct from v_owner::text then raise exception 'Storage owner mismatch'; end if;
 select * into p from public.posts where video_path=p_path;
 if p.id is not null and p.user_id is distinct from v_owner then raise exception 'post owner mismatch'; end if;
 return jsonb_build_object('owner',v_owner,'path',p_path,'sha256',m.sha256,'size',m.size_bytes,'type',m.media_type,
 'content',m.content,'expires',extract(epoch from m.expires_at)::bigint,
 'active',m.expires_at>clock_timestamp() and r.created_at+interval '1 hour'>clock_timestamp(),
 'generation',o.id,'post_id',p.id,'post_generation',p.video_generation,'post_sha256',p.video_sha256,'post_duration',p.video_duration_seconds);
end $$;
revoke all on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) from public,anon,service_role;
revoke all on function public.video_recovery_state_v1(text) from public,anon,service_role;
grant execute on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) to authenticated;
grant execute on function public.video_recovery_state_v1(text) to authenticated;

-- Private, volatile check: PostgREST validates JWTs at request admission, but
-- a reservation/Storage lock wait can cross expiry or a session revocation.
-- Lock the exact Auth session AFTER reservation acquisition so revocation
-- during that wait is observable; key-share fences deletion until commit.
create or replace function video_private.assert_recovery_identity(p_owner uuid)
returns void language plpgsql volatile security definer set search_path='' as $$
declare v_exp text := auth.jwt()->>'exp'; v_session text := auth.jwt()->>'session_id';
begin
 if p_owner is null or auth.uid() is distinct from p_owner or
 v_exp is null or v_exp !~ '^[0-9]{1,12}$' or
 v_session is null or v_session !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
 then raise exception 'recovery identity unavailable'; end if;
 if v_exp::numeric <= extract(epoch from clock_timestamp()) then raise exception 'recovery JWT expired'; end if;
 perform 1 from auth.sessions where id=v_session::uuid and user_id=p_owner
 and (not_after is null or not_after>clock_timestamp()) for key share;
 if not found then raise exception 'recovery session unavailable'; end if;
 -- The session lookup itself can wait on Auth, so re-evaluate the clock.
 if auth.uid() is distinct from p_owner or v_exp::numeric <= extract(epoch from clock_timestamp())
 then raise exception 'recovery JWT expired'; end if;
end $$;
revoke all on function video_private.assert_recovery_identity(uuid) from public,anon,authenticated,service_role;

-- Recovery-specific atomic publication fence. A read-only status result is
-- never authority: recheck owner, expiry and original hash in the transaction
-- that validates HMAC/generation/nonce and inserts/reconciles the post.
create or replace function public.video_publish_recovered_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype; v_id uuid;
begin
 if p_owner is null or (select auth.uid()) is distinct from p_owner then raise exception 'recovery owner mismatch'; end if;
 -- Match parent publish's reservation-before-Storage lock order.
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'recovery reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=p_owner for update;
 if not found or m.expires_at<=clock_timestamp() or m.sha256 is distinct from p_sha256 or m.content is distinct from p_content then raise exception 'recovery manifest mismatch or expired'; end if;
 perform video_private.assert_recovery_identity(p_owner);
 v_id:=public.video_publish_attested_v1(p_owner,p_path,p_generation,p_sha256,p_duration_ms,p_content,p_expires_at,p_nonce,p_signature,p_key_id);
 -- A lock wait inside parent publication must not outlive auth or either deadline.
 perform video_private.assert_recovery_identity(p_owner);
 if m.expires_at<=clock_timestamp() or r.created_at+interval '1 hour'<=clock_timestamp() or
 p_expires_at<=extract(epoch from clock_timestamp())::bigint then raise exception 'recovery expired during publication'; end if;
 return v_id;
end $$;
revoke all on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,service_role;
grant execute on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;

commit;
)
);
revoke all on video_private.recovery_migration_seal from public,anon,authenticated,service_role;
alter table video_private.recovery_manifests enable row level security;
revoke all on video_private.recovery_manifests from public,anon,authenticated,service_role;

create or replace function public.video_bind_recovery_manifest_v1(p_path text,p_sha256 text,p_size integer,p_type text,p_content text)
returns bigint language plpgsql security definer set search_path='' as $$
declare r public.video_reserved_object_keys%rowtype; m video_private.recovery_manifests%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text or
 p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_size is null or p_size not between 1 and 20971520 or
 p_content is null or length(p_content)>10000 or p_type is null or p_type not in ('video/mp4','video/webm') or
 not ( (p_type='video/mp4' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]mp4$') or
       (p_type='video/webm' and p_path ~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.]webm$') )
 then raise exception 'invalid recovery manifest'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path;
 if found then
   if m.owner_id is distinct from v_owner or m.sha256 is distinct from p_sha256 or m.size_bytes is distinct from p_size or m.media_type is distinct from p_type or m.content is distinct from p_content then raise exception 'conflicting recovery manifest'; end if;
   return extract(epoch from m.expires_at)::bigint;
 end if;
 -- Binding existing objects/posts after a restart would let local hints invent
 -- original-file identity. Only a pre-upload manifest is eligible.
 if exists(select 1 from storage.objects where bucket_id='post-videos' and name=p_path) or
 exists(select 1 from public.posts where video_path=p_path) then raise exception 'manifest must precede upload'; end if;
 insert into video_private.recovery_manifests(object_path,owner_id,sha256,size_bytes,media_type,content,expires_at) values(p_path,v_owner,p_sha256,p_size,p_type,p_content,r.created_at+interval '1 hour');
 return extract(epoch from r.created_at+interval '1 hour')::bigint;
end $$;

create or replace function public.video_recovery_state_v1(p_path text)
returns jsonb language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype;
 o storage.objects%rowtype; p public.posts%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text then raise exception 'recovery owner mismatch'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=v_owner;
 if not found then raise exception 'recovery manifest unavailable'; end if;
 select * into o from storage.objects where bucket_id='post-videos' and name=p_path;
 if o.id is not null and o.owner_id is distinct from v_owner::text then raise exception 'Storage owner mismatch'; end if;
 select * into p from public.posts where video_path=p_path;
 if p.id is not null and p.user_id is distinct from v_owner then raise exception 'post owner mismatch'; end if;
 return jsonb_build_object('owner',v_owner,'path',p_path,'sha256',m.sha256,'size',m.size_bytes,'type',m.media_type,
 'content',m.content,'expires',extract(epoch from m.expires_at)::bigint,
 'active',m.expires_at>clock_timestamp() and r.created_at+interval '1 hour'>clock_timestamp(),
 'generation',o.id,'post_id',p.id,'post_generation',p.video_generation,'post_sha256',p.video_sha256,'post_duration',p.video_duration_seconds);
end $$;
revoke all on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) from public,anon,service_role;
revoke all on function public.video_recovery_state_v1(text) from public,anon,service_role;
grant execute on function public.video_bind_recovery_manifest_v1(text,text,integer,text,text) to authenticated;
grant execute on function public.video_recovery_state_v1(text) to authenticated;

-- Private, volatile check: PostgREST validates JWTs at request admission, but
-- a reservation/Storage lock wait can cross expiry or a session revocation.
-- Lock the exact Auth session AFTER reservation acquisition so revocation
-- during that wait is observable; key-share fences deletion until commit.
create or replace function video_private.assert_recovery_identity(p_owner uuid)
returns void language plpgsql volatile security definer set search_path='' as $$
declare v_exp text := auth.jwt()->>'exp'; v_session text := auth.jwt()->>'session_id';
begin
 if p_owner is null or auth.uid() is distinct from p_owner or
 v_exp is null or v_exp !~ '^[0-9]{1,12}$' or
 v_session is null or v_session !~ '^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$'
 then raise exception 'recovery identity unavailable'; end if;
 if v_exp::numeric <= extract(epoch from clock_timestamp()) then raise exception 'recovery JWT expired'; end if;
 perform 1 from auth.sessions where id=v_session::uuid and user_id=p_owner
 and (not_after is null or not_after>clock_timestamp()) for key share;
 if not found then raise exception 'recovery session unavailable'; end if;
 -- The session lookup itself can wait on Auth, so re-evaluate the clock.
 if auth.uid() is distinct from p_owner or v_exp::numeric <= extract(epoch from clock_timestamp())
 then raise exception 'recovery JWT expired'; end if;
end $$;
revoke all on function video_private.assert_recovery_identity(uuid) from public,anon,authenticated,service_role;

-- Recovery-specific atomic publication fence. A read-only status result is
-- never authority: recheck owner, expiry and original hash in the transaction
-- that validates HMAC/generation/nonce and inserts/reconciles the post.
create or replace function public.video_publish_recovered_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $$
declare m video_private.recovery_manifests%rowtype; r public.video_reserved_object_keys%rowtype; v_id uuid;
begin
 if p_owner is null or (select auth.uid()) is distinct from p_owner then raise exception 'recovery owner mismatch'; end if;
 -- Match parent publish's reservation-before-Storage lock order.
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'recovery reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path and owner_id=p_owner for update;
 if not found or m.expires_at<=clock_timestamp() or m.sha256 is distinct from p_sha256 or m.content is distinct from p_content then raise exception 'recovery manifest mismatch or expired'; end if;
 perform video_private.assert_recovery_identity(p_owner);
 v_id:=public.video_publish_attested_v1(p_owner,p_path,p_generation,p_sha256,p_duration_ms,p_content,p_expires_at,p_nonce,p_signature,p_key_id);
 -- A lock wait inside parent publication must not outlive auth or either deadline.
 perform video_private.assert_recovery_identity(p_owner);
 if m.expires_at<=clock_timestamp() or r.created_at+interval '1 hour'<=clock_timestamp() or
 p_expires_at<=extract(epoch from clock_timestamp())::bigint then raise exception 'recovery expired during publication'; end if;
 return v_id;
end $$;
revoke all on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,service_role;
grant execute on function public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;

-- Seal the exact SQL function definitions after first install. Identical reapply
-- is safe, while a future human/manual edit requires explicit review.
insert into video_private.recovery_migration_seal(version,definition_digest)
values ('recovery-v1',md5(
  pg_get_functiondef('public.video_bind_recovery_manifest_v1(text,text,integer,text,text)'::regprocedure) ||
  pg_get_functiondef('public.video_recovery_state_v1(text)'::regprocedure) ||
  pg_get_functiondef('video_private.assert_recovery_identity(uuid)'::regprocedure) ||
  pg_get_functiondef('public.video_publish_recovered_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)'::regprocedure)
))
on conflict (version) do nothing;

commit;

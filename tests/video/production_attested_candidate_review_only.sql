-- REVIEW ONLY: append to production_additive_candidate.sql only after disposable QA.
-- Provision key via separate DBA-controlled transaction, never in source or migration.
-- This table is not in an exposed PostgREST schema.
create schema if not exists video_private;
revoke all on schema video_private from public,anon,authenticated,service_role;
create table if not exists video_private.attestation_keys(
 key_id smallint primary key, secret bytea not null check(octet_length(secret)=32), active boolean not null default false
);
revoke all on video_private.attestation_keys from public,anon,authenticated,service_role;
create table if not exists video_private.consumed_nonces(
 nonce bytea primary key check(octet_length(nonce)=16), owner_id uuid not null,
 object_path text not null, created_at timestamptz not null default now()
);
revoke all on video_private.consumed_nonces from public,anon,authenticated,service_role;
-- The signing secret must be installed separately and atomically on both server and DB.
-- PostgreSQL pgcrypto is required; no secret or provisioning endpoint is exposed.
create extension if not exists pgcrypto;
create or replace function public.video_publish_attested_v1(
 p_owner uuid,p_path text,p_generation uuid,p_sha256 text,p_duration_ms integer,
 p_content text,p_expires_at bigint,p_nonce text,p_signature text,p_key_id smallint
) returns uuid language plpgsql security definer set search_path='' as $fn$
declare
 v_secret bytea;v_payload bytea;v_expected bytea;v_signature bytea;
 v_path bytea;v_id uuid;v_existing public.posts%rowtype;
begin
 if (select auth.uid()) is distinct from p_owner then raise exception 'video owner mismatch'; end if;
 if p_owner is null or p_generation is null or p_path is null or
  p_path !~ ('^'||p_owner::text||'/[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}[.](mp4|webm)$') or
  p_sha256 !~ '^[0-9a-f]{64}$' or p_nonce !~ '^[0-9a-f]{32}$' or
  p_signature !~ '^[0-9a-f]{64}$' or p_duration_ms not between 1 and 30000 or
  p_content is null or length(p_content)>10000 or
  p_expires_at <= extract(epoch from clock_timestamp())::bigint or
  p_expires_at > extract(epoch from clock_timestamp())::bigint+300 or
  p_expires_at<0 then raise exception 'invalid attestation claims'; end if;
 v_path:=convert_to(p_path,'UTF8');
 if octet_length(v_path)>255 then raise exception 'path too long'; end if;
 select secret into v_secret from video_private.attestation_keys where key_id=p_key_id and active=true;
 if v_secret is null then raise exception 'attestation key unavailable'; end if;
 v_payload:=decode('01','hex')||decode(replace(p_owner::text,'-',''),'hex')||
  set_byte(decode('00','hex'),0,octet_length(v_path))||v_path||
  decode(replace(p_generation::text,'-',''),'hex')||decode(p_sha256,'hex')||
  pg_catalog.int4send(p_duration_ms)||
  extensions.digest(convert_to(p_content,'UTF8'),'sha256')||
  pg_catalog.int8send(p_expires_at)||decode(p_nonce,'hex');
 v_expected:=extensions.hmac(v_payload,v_secret,'sha256');
 v_signature:=decode(p_signature,'hex');
 -- Compare all bytes, with no early exit on mismatched prefix.
 if octet_length(v_expected)<>octet_length(v_signature) or
   (select bit_or(get_byte(v_expected,n) # get_byte(v_signature,n))
    from generate_series(0,31) as n)<>0 then
  raise exception 'invalid video attestation'; end if;
 perform 1 from public.video_reserved_object_keys
  where bucket_id='post-videos' and object_path=p_path and owner_id=p_owner for update;
 if not found then raise exception 'missing owner reservation'; end if;
 perform 1 from storage.objects where bucket_id='post-videos' and name=p_path
  and id=p_generation and owner_id=p_owner::text for update;
 if not found then raise exception 'Storage generation mismatch'; end if;
 -- Single-use nonce is consumed in the SAME transaction as post publication.
 insert into video_private.consumed_nonces(nonce,owner_id,object_path)
 values(decode(p_nonce,'hex'),p_owner,p_path);
 insert into public.posts(user_id,content,post_type,image_urls,video_path,
  video_generation,video_sha256,video_duration_seconds)
 values(p_owner,p_content,'normal','{}'::text[],p_path,p_generation,p_sha256,p_duration_ms::double precision/1000)
 on conflict(video_path) where video_path is not null do nothing returning id into v_id;
 if v_id is null then
  select * into v_existing from public.posts where video_path=p_path;
  if v_existing.user_id<>p_owner or v_existing.video_generation<>p_generation or
   v_existing.video_sha256<>p_sha256 or
   v_existing.video_duration_seconds<>p_duration_ms::double precision/1000 or
   v_existing.content<>p_content then raise exception 'conflicting prior video publication'; end if;
  v_id:=v_existing.id;
 end if;
 if v_id is null then raise exception 'publication failed'; end if;
 return v_id;
end $fn$;
revoke all on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) from public,anon,service_role;
-- Grant to authenticated only after production-equivalent isolated tests and secret provisioning.
-- grant execute on function public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint) to authenticated;

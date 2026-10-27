-- REVIEW ONLY. Applied exclusively to disposable isolated CI, never production.
create schema if not exists video_private;
revoke all on schema video_private from public,anon,authenticated,service_role;
create table if not exists video_private.recovery_manifests (
 object_path text primary key,
 bucket_id text not null default 'post-videos' check(bucket_id='post-videos'),
 foreign key(bucket_id,object_path) references public.video_reserved_object_keys(bucket_id,object_path),
 owner_id uuid not null, sha256 text not null check(sha256 ~ '^[0-9a-f]{64}$'),
 size_bytes integer not null check(size_bytes between 1 and 20971520),
 media_type text not null check(media_type in ('video/mp4','video/webm')),
 expires_at timestamptz not null
);
alter table video_private.recovery_manifests enable row level security;
revoke all on video_private.recovery_manifests from public,anon,authenticated,service_role;

create or replace function public.video_bind_recovery_manifest_v1(p_path text,p_sha256 text,p_size integer,p_type text)
returns bigint language plpgsql security definer set search_path='' as $$
declare r public.video_reserved_object_keys%rowtype; m video_private.recovery_manifests%rowtype; v_owner uuid := auth.uid();
begin
 if v_owner is null or p_path is null or split_part(p_path,'/',1) is distinct from v_owner::text or
 p_sha256 is null or p_sha256 !~ '^[0-9a-f]{64}$' or p_size is null or p_size not between 1 and 20971520 or
 p_type is null or p_type not in ('video/mp4','video/webm') or
 (p_type='video/mp4') is distinct from (right(p_path,4)='.mp4') then raise exception 'invalid recovery manifest'; end if;
 select * into r from public.video_reserved_object_keys where bucket_id='post-videos' and object_path=p_path and owner_id=v_owner for update;
 if not found or r.created_at+interval '1 hour' <= clock_timestamp() then raise exception 'reservation unavailable'; end if;
 select * into m from video_private.recovery_manifests where object_path=p_path;
 if found then
   if m.owner_id is distinct from v_owner or m.sha256 is distinct from p_sha256 or m.size_bytes is distinct from p_size or m.media_type is distinct from p_type then raise exception 'conflicting recovery manifest'; end if;
   return extract(epoch from m.expires_at)::bigint;
 end if;
 -- Binding existing objects/posts after a restart would let local hints invent
 -- original-file identity. Only a pre-upload manifest is eligible.
 if exists(select 1 from storage.objects where bucket_id='post-videos' and name=p_path) or
 exists(select 1 from public.posts where video_path=p_path) then raise exception 'manifest must precede upload'; end if;
 insert into video_private.recovery_manifests(object_path,owner_id,sha256,size_bytes,media_type,expires_at) values(p_path,v_owner,p_sha256,p_size,p_type,r.created_at+interval '1 hour');
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
 'expires',extract(epoch from m.expires_at)::bigint,
 'active',m.expires_at>clock_timestamp() and r.created_at+interval '1 hour'>clock_timestamp(),
 'generation',o.id,'post_id',p.id,'post_generation',p.video_generation,'post_sha256',p.video_sha256,'post_duration',p.video_duration_seconds);
end $$;
revoke all on function public.video_bind_recovery_manifest_v1(text,text,integer,text) from public,anon,service_role;
revoke all on function public.video_recovery_state_v1(text) from public,anon,service_role;
grant execute on function public.video_bind_recovery_manifest_v1(text,text,integer,text) to authenticated;
grant execute on function public.video_recovery_state_v1(text) to authenticated;

-- Review only. Initial rollout candidate. Never run from an automated deploy.
-- Replacing the function preserves its existing owner and EXECUTE grants.
begin;
create table video_private.usage_budget (
 singleton boolean primary key default true check(singleton),
 enabled boolean not null default false,
 reads_enabled boolean not null default false,
 reader_id uuid,
 meter_key_sha256 bytea,
 account_hourly integer not null default 3 check(account_hourly > 0),
 account_daily integer not null default 5 check(account_daily > 0),
 shared_daily integer not null default 5 check(shared_daily > 0),
 shared_total integer not null default 24 check(shared_total > 0),
 monthly_read_bytes bigint not null default 1000000000 check(monthly_read_bytes > 0),
 monthly_delivery_bytes bigint not null default 1000000000 check(monthly_delivery_bytes > 0),
 monthly_operations integer not null default 1000 check(monthly_operations > 0)
);
insert into video_private.usage_budget default values;

create table video_private.usage_budget_month (
 month_utc date primary key,
 read_bytes bigint not null default 0,
 delivery_bytes bigint not null default 0,
 operations integer not null default 0
);
revoke all on video_private.usage_budget, video_private.usage_budget_month from public, anon, authenticated, service_role;

create function public.video_meter_operation(p_operation text, p_key text)
returns boolean language plpgsql security definer set search_path='' as $$
declare
 settings video_private.usage_budget%rowtype;
 month_key date := date_trunc('month',now() at time zone 'UTC')::date;
 delivery_cost integer := 0;
begin
 if p_operation is null or p_operation not in ('media','finalize','inspect') or
    p_key is null or length(p_key) <> 64 or not public.video_rollout_allowed() then return false; end if;
 select * into settings from video_private.usage_budget where singleton for share;
 if not found or not settings.enabled or not settings.reads_enabled or settings.reader_id is null or
    settings.meter_key_sha256 is distinct from pg_catalog.sha256(pg_catalog.convert_to(p_key,'UTF8')) then
   return false;
 end if;
 if p_operation='media' then delivery_cost := 20971520; end if;
 insert into video_private.usage_budget_month(month_utc) values(month_key) on conflict do nothing;
 update video_private.usage_budget_month
 set read_bytes=read_bytes+20971520, delivery_bytes=delivery_bytes+delivery_cost, operations=operations+1
 where month_utc=month_key and read_bytes+20971520<=settings.monthly_read_bytes
   and delivery_bytes+delivery_cost<=settings.monthly_delivery_bytes and operations<settings.monthly_operations;
 return found;
end $$;
revoke all on function public.video_meter_operation(text,text) from public, anon, service_role;
grant execute on function public.video_meter_operation(text,text) to authenticated;

-- A dedicated Auth account is a scoped reader. Storage never sees the caller
-- as this account. It cannot reserve or publish on behalf of other users.
create function public.video_budget_storage_reader()
returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from video_private.usage_budget
   where singleton and enabled and reads_enabled and reader_id=auth.uid())
$$;
create function public.video_budget_legacy_reads()
returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from video_private.usage_budget where singleton and not enabled)
   and not exists(select 1 from video_private.general_public_rollout where singleton and enabled)
$$;
revoke all on function public.video_budget_storage_reader(), public.video_budget_legacy_reads() from public, anon, service_role;
grant execute on function public.video_budget_storage_reader(), public.video_budget_legacy_reads() to authenticated;
alter policy video_rollout_storage_read on storage.objects
 using (bucket_id <> 'post-videos' or public.video_budget_storage_reader() or
   (public.video_budget_legacy_reads() and public.video_rollout_member() and public.video_rollout_visible(name)));
create policy video_budget_scoped_reader on storage.objects for select to authenticated
 using (bucket_id='post-videos' and public.video_budget_storage_reader());

CREATE OR REPLACE FUNCTION public.video_reserve_object_key(p_owner uuid, p_path text)
 RETURNS uuid
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare
  v_id uuid;
  settings video_private.usage_budget%rowtype;
begin
  if not public.video_rollout_allowed() then raise exception 'video rollout disabled'; end if;
  -- Caller identity is the sole reservation authority; do not trust p_owner.
  if (select auth.uid()) is distinct from p_owner then
    raise exception 'reservation owner mismatch';
  end if;
  if p_owner is null or p_path is null
     or p_path !~ ('^' || p_owner::text ||
       '/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}[.](mp4|webm)$')
  then
    raise exception 'invalid video reservation';
  end if;
  -- Serialize reservations per owner to prevent concurrent calls bypassing
  -- rolling-window quotas. This ledger is append-only, so abandoned uploads
  -- consume quota instead of allowing unbounded permanent key reservations.
  perform pg_catalog.pg_advisory_xact_lock(pg_catalog.hashtextextended(p_owner::text, 72941));
  -- Serialize the shared allowance before counting or consuming a slot.
  perform pg_catalog.pg_advisory_xact_lock(72941, 134);
  select * into strict settings from video_private.usage_budget where singleton for share;
  if not settings.enabled and not public.video_budget_legacy_reads() then
    raise exception 'video budget unavailable';
  end if;
  if settings.enabled and (not settings.reads_enabled or settings.reader_id is null or
     settings.meter_key_sha256 is null or settings.reader_id=p_owner) then
    raise exception 'video budget stopped';
  end if;
  if (select count(*) from public.video_reserved_object_keys where bucket_id='post-videos') >= settings.shared_total
     or (select count(*) from public.video_reserved_object_keys
         where bucket_id='post-videos' and created_at>pg_catalog.clock_timestamp()-interval '24 hours') >= settings.shared_daily
  then
    raise exception 'video shared reservation limit exceeded';
  end if;
  if (select count(*) from public.video_reserved_object_keys
      where owner_id=p_owner and created_at>pg_catalog.clock_timestamp()-interval '1 hour') >= settings.account_hourly
     or (select count(*) from public.video_reserved_object_keys
      where owner_id=p_owner and created_at>pg_catalog.clock_timestamp()-interval '24 hours') >= settings.account_daily
  then
    raise exception 'video reservation rate limit exceeded';
  end if;
  -- Do not use ON CONFLICT DO UPDATE or return an existing reservation.
  -- A collision must fail permanently, including a deleted Storage object.
  insert into public.video_reserved_object_keys(bucket_id,object_path,owner_id)
    values ('post-videos',p_path,p_owner)
    returning reservation_id into v_id;
  return v_id;
end;
$function$;
commit;

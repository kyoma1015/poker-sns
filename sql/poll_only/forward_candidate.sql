-- REVIEW CANDIDATE ONLY. Never run against production without catalog/backup review.
-- Prerequisites: existing application posts/profiles/user_blocks/notifications,
-- and the original post_interactive + responses tables (all historical rows kept).
begin;
set local lock_timeout = '5s';
set local statement_timeout = '30s';
-- Fail closed when basic application dependencies are absent. This is not a base schema migration.
do $$
begin
 if to_regclass('public.posts') is null or to_regclass('public.profiles') is null
 or to_regclass('public.user_blocks') is null or to_regclass('public.notifications') is null
 or to_regclass('public.post_interactive') is null or to_regclass('public.post_interactive_responses') is null then
   raise exception 'Poll prerequisites missing; do not reconstruct production from historical SQL alone';
 end if;
 if exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname like 'create_interactive_post%'
   and (p.proname || ':' || oidvectortypes(p.proargtypes)) not in
    ('create_interactive_post:text, text, text[], integer',
     'create_interactive_post_v2:text, text, text[], integer, boolean',
     'create_interactive_post_v3:text, text, text[], integer, boolean, text',
     'create_interactive_post_v4:text, text, text[], integer, boolean, text')) then
   raise exception 'Unknown legacy creation overload: catalog review required';
 end if;
 if exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and ((p.proname like 'get_interactive_results%' and p.proname not in ('get_interactive_results','get_interactive_results_v4'))
 or (p.proname like 'submit_interactive_response%' and p.proname not in ('submit_interactive_response','submit_interactive_response_v2')))) then
  raise exception 'Unknown historical read/write RPC: privacy catalog review required';
 end if;
end $$;
alter table public.post_interactive add column if not exists is_anonymous boolean not null default true;
do $$begin
 if exists(select 1 from public.post_interactive where is_anonymous is null) then raise exception 'Unknown NULL privacy mode: owner review required'; end if;
 if (select atttypid from pg_attribute where attrelid='public.post_interactive'::regclass and attname='is_anonymous') <> 'boolean'::regtype then raise exception 'Incompatible privacy column'; end if;
end$$;
alter table public.post_interactive enable row level security;
alter table public.post_interactive_responses enable row level security;
-- Known historical policy still grants metadata visibility, including the kind
-- marker needed by old-data hiding in the UI. No table writes are client APIs.
revoke insert, update, delete on public.post_interactive, public.post_interactive_responses from public, anon, authenticated;
grant select on public.post_interactive to authenticated;
drop policy if exists poll_metadata_visibility_v1 on public.post_interactive;
create policy poll_metadata_visibility_v1 on public.post_interactive as restrictive for select to authenticated
 using ((select auth.uid()) is not null and exists (select 1 from public.posts p where p.id=post_id)
 and not exists (select 1 from public.posts p join public.user_blocks b on
   (b.blocker_id=p.user_id and b.blocked_id=(select auth.uid())) or
   (b.blocked_id=p.user_id and b.blocker_id=(select auth.uid())) where p.id=post_id));
-- Prevent ANY permissive policy (including an old own-row policy) from exposing
-- poll identity/timestamp columns through direct REST. Question data is retained.
drop policy if exists poll_raw_identity_guard_v1 on public.post_interactive_responses;
create policy poll_raw_identity_guard_v1 on public.post_interactive_responses as restrictive for select to authenticated
 using (exists (select 1 from public.post_interactive i where i.post_id=post_interactive_responses.post_id and i.kind='question'));

create schema if not exists poll_private;
revoke all on schema poll_private from public, anon, authenticated;
create table if not exists poll_private.close_receipts (
 post_id uuid primary key references public.post_interactive(post_id),
 notification_id uuid not null unique,
 created_at timestamptz not null default now()
);
alter table poll_private.close_receipts enable row level security;
revoke all on poll_private.close_receipts from public, anon, authenticated;

create or replace function poll_private.assert_visible(p_post_id uuid) returns void
language plpgsql security definer set search_path='' as $$
declare v_user uuid:=auth.uid();
begin
 if v_user is null then raise exception 'Login required' using errcode='42501'; end if;
 if not exists(select 1 from public.posts where id=p_post_id) or exists (
 select 1 from public.posts p join public.user_blocks b on
  (b.blocker_id=p.user_id and b.blocked_id=v_user) or
  (b.blocked_id=p.user_id and b.blocker_id=v_user) where p.id=p_post_id) then
  raise exception 'Post unavailable' using errcode='42501';
 end if;
end $$;
revoke all on function poll_private.assert_visible(uuid) from public, anon, authenticated;

create or replace function public.create_interactive_post_v4(p_content text,p_kind text,p_options text[] default null,p_hours integer default 24,p_is_anonymous boolean default true,p_question_policy text default null)
returns uuid language plpgsql security definer set search_path='' as $$
declare v_user uuid:=auth.uid();v_id uuid;v_options text[];
begin
 if v_user is null then raise exception 'Login required' using errcode='42501'; end if;
 if p_kind is distinct from 'poll' or p_question_policy is not null then raise exception 'Polls only' using errcode='22023'; end if;
 if char_length(btrim(coalesce(p_content,''))) not between 1 and 500 or p_is_anonymous is null
 or p_hours is null or p_hours not in (1,6,24,72,168) or coalesce(array_ndims(p_options),0)<>1
 or coalesce(cardinality(p_options),0) not between 2 and 4 then raise exception 'Invalid poll settings' using errcode='22023'; end if;
 select array_agg(btrim(v) order by ord) into v_options from unnest(p_options) with ordinality t(v,ord);
 if exists(select 1 from unnest(v_options) v where char_length(coalesce(v,'')) not between 1 and 80)
 or (select count(distinct lower(v)) from unnest(v_options) v)<>cardinality(v_options) then raise exception 'Invalid or duplicate options' using errcode='22023'; end if;
 insert into public.posts(user_id,content,post_type,result_type,result_id) values(v_user,btrim(p_content),'normal',null,null) returning id into v_id;
 insert into public.post_interactive(post_id,kind,options,closes_at,is_anonymous) values(v_id,'poll',to_jsonb(v_options),statement_timestamp()+make_interval(hours=>p_hours),p_is_anonymous);
 return v_id;
end $$;
create or replace function public.create_interactive_post(p_content text,p_kind text,p_options text[] default null,p_hours integer default 24)
returns uuid language sql security invoker set search_path='' as $$select public.create_interactive_post_v4(p_content,p_kind,p_options,p_hours,true,null)$$;
create or replace function public.create_interactive_post_v2(p_content text,p_kind text,p_options text[] default null,p_hours integer default 24,p_is_anonymous boolean default true)
returns uuid language sql security invoker set search_path='' as $$select public.create_interactive_post_v4(p_content,p_kind,p_options,p_hours,p_is_anonymous,null)$$;
create or replace function public.create_interactive_post_v3(p_content text,p_kind text,p_options text[] default null,p_hours integer default 24,p_is_anonymous boolean default true,p_question_policy text default null)
returns uuid language sql security invoker set search_path='' as $$select public.create_interactive_post_v4(p_content,p_kind,p_options,p_hours,p_is_anonymous,p_question_policy)$$;

create or replace function public.submit_interactive_response_v2(p_post_id uuid,p_option_index integer default null,p_answer text default null,p_is_anonymous boolean default true)
returns void language plpgsql security definer set search_path='' as $$
declare v_item public.post_interactive%rowtype;
begin
 perform poll_private.assert_visible(p_post_id);
 select * into v_item from public.post_interactive where post_id=p_post_id for share;
 if not found or v_item.kind<>'poll' then raise exception 'Polls only' using errcode='22023'; end if;
 if v_item.closes_at<=clock_timestamp() then raise exception 'Poll closed' using errcode='22023'; end if;
 if p_answer is not null or p_option_index is null or p_option_index<0 or p_option_index>=jsonb_array_length(v_item.options)
 or p_is_anonymous is distinct from v_item.is_anonymous then raise exception 'Invalid vote/privacy mode' using errcode='22023'; end if;
 insert into public.post_interactive_responses(post_id,user_id,option_index,answer) values(p_post_id,auth.uid(),p_option_index,null);
end $$;
create or replace function public.submit_interactive_response(p_post_id uuid,p_option_index integer default null,p_answer text default null)
returns void language plpgsql security definer set search_path='' as $$
declare v_anonymous boolean;
begin
 perform poll_private.assert_visible(p_post_id);
 select is_anonymous into v_anonymous from public.post_interactive where post_id=p_post_id;
 perform public.submit_interactive_response_v2(p_post_id,p_option_index,p_answer,v_anonymous);
end $$;

create or replace function public.get_interactive_results_v4(p_post_ids uuid[])
returns table(post_id uuid,total_votes bigint,vote_counts jsonb,answers jsonb,my_option_index integer,has_responded boolean,voters jsonb)
language plpgsql stable security definer set search_path='' as $$
declare v_item public.post_interactive%rowtype; v_user uuid:=auth.uid();
begin
 if v_user is null then raise exception 'Login required' using errcode='42501'; end if;
 if coalesce(cardinality(p_post_ids),0)>500 then raise exception 'Too many IDs' using errcode='22023'; end if;
 for v_item in select * from public.post_interactive i where i.post_id=any(p_post_ids) and i.kind='poll' loop
  perform poll_private.assert_visible(v_item.post_id);
  return query select v_item.post_id,
   (select count(*) from public.post_interactive_responses r where r.post_id=v_item.post_id),
   (select coalesce(jsonb_object_agg(t.option_index::text,t.cnt),'{}'::jsonb) from
     (select r.option_index,count(*) cnt from public.post_interactive_responses r where r.post_id=v_item.post_id group by r.option_index) t),
   '[]'::jsonb,
   (select r.option_index from public.post_interactive_responses r where r.post_id=v_item.post_id and r.user_id=v_user),
   exists(select 1 from public.post_interactive_responses r where r.post_id=v_item.post_id and r.user_id=v_user),
   case when v_item.is_anonymous is not false then '[]'::jsonb else
    (select coalesce(jsonb_agg(jsonb_build_object('option_index',r.option_index,'poker_id',p.poker_id,'display_name',p.display_name,'avatar_url',p.avatar_url)),'[]'::jsonb)
     from public.post_interactive_responses r join public.profiles p on p.id=r.user_id where r.post_id=v_item.post_id) end;
 end loop;
end $$;
create or replace function public.get_interactive_results(p_post_ids uuid[])
returns table(post_id uuid,total_votes bigint,vote_counts jsonb,answers jsonb,my_option_index integer,has_responded boolean)
language sql stable security invoker set search_path='' as $$ select r.post_id,r.total_votes,r.vote_counts,r.answers,r.my_option_index,r.has_responded from public.get_interactive_results_v4(p_post_ids) r $$;

-- A restrictive policy combines with every existing permissive INSERT policy.
-- It does not revoke the legacy INSERT grant or block like/comment/follow.
drop policy if exists poll_closed_forgery_guard_v1 on public.notifications;
create policy poll_closed_forgery_guard_v1 on public.notifications as restrictive for insert to anon,authenticated with check (type<>'poll_closed');
create or replace function poll_private.guard_closed_notification() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if (new.type='poll_closed' or (tg_op='UPDATE' and old.type='poll_closed')) and
    (auth.uid() is not null or coalesce(current_setting('role',true),'none') not in ('none','postgres','service_role')) then
  if tg_op='INSERT' or (to_jsonb(new)-'read_at') is distinct from (to_jsonb(old)-'read_at') then
   raise exception 'System poll notifications are immutable' using errcode='42501';
  end if;
 end if;
 return new;
end $$;
revoke all on function poll_private.guard_closed_notification() from public,anon,authenticated;
drop trigger if exists poll_closed_guard_v1 on public.notifications;
create trigger poll_closed_guard_v1 before insert or update on public.notifications for each row execute function poll_private.guard_closed_notification();

create or replace function poll_private.close_due_polls() returns integer
language plpgsql security definer set search_path='' as $$
declare r record; v_id uuid; v_claim uuid; v_count integer:=0;
begin
 for r in select i.post_id,p.user_id from public.post_interactive i join public.posts p on p.id=i.post_id
  where i.kind='poll' and i.closes_at<=clock_timestamp() and not exists(select 1 from poll_private.close_receipts c where c.post_id=i.post_id)
  order by i.closes_at for update of i skip locked loop
   v_id:=gen_random_uuid();v_claim:=null;
   insert into poll_private.close_receipts(post_id,notification_id) values(r.post_id,v_id) on conflict do nothing returning post_id into v_claim;
   if v_claim is not null then
    if exists(select 1 from information_schema.columns where table_schema='public' and table_name='notifications' and column_name='event_key') then
     execute 'insert into public.notifications(id,user_id,actor_id,type,post_id,event_key) values($1,$2,$2,''poll_closed'',$3,$4)' using v_id,r.user_id,r.post_id,'poll_closed:'||r.post_id::text;
    else
     insert into public.notifications(id,user_id,actor_id,type,post_id) values(v_id,r.user_id,r.user_id,'poll_closed',r.post_id);
    end if;
    v_count:=v_count+1;
   end if;
 end loop;
 return v_count;
end $$;
revoke all on function poll_private.close_due_polls() from public,anon,authenticated;
create or replace function public.finish_due_polls_v1() returns integer language sql security invoker set search_path='' as $$select poll_private.close_due_polls()$$;
revoke all on function public.finish_due_polls_v1() from public,anon,authenticated;
-- Retire any legacy client-executable close RPC without touching notification
-- table INSERT grants. Unknown cron definitions are separately a review gate.
do $$declare r record;begin
 for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and (p.proname like 'finish_due_poll%' or p.proname like 'close%poll%' or p.proname like 'process%poll%' or p.proname like 'finish_due_interactive%') loop
  execute format('revoke execute on function %s from public,anon,authenticated',r.sig);
 end loop;
end$$;
-- The scheduler is installed explicitly by the owner using the separate file.
-- Do not give an untrusted REST client a system close RPC.

do $$
declare r record;
begin
 for r in select p.oid::regprocedure sig from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in ('create_interactive_post','create_interactive_post_v2','create_interactive_post_v3','create_interactive_post_v4','submit_interactive_response','submit_interactive_response_v2','get_interactive_results','get_interactive_results_v4') loop
 execute format('revoke all on function %s from public,anon',r.sig);
 execute format('grant execute on function %s to authenticated',r.sig);
 end loop;
end $$;
notify pgrst, 'reload schema';
commit;

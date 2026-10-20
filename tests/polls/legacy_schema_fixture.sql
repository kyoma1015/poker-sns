-- Poker ID: timeline polls and question boxes (review before production deployment)
create table if not exists public.post_interactive (
 post_id uuid primary key references public.posts(id) on delete cascade,
 kind text not null check (kind in ('poll','question')),
 options jsonb not null default '[]'::jsonb,
 closes_at timestamptz,
 created_at timestamptz not null default now(),
 constraint poll_options_valid check (
  (kind='question' and options='[]'::jsonb and closes_at is null)
  or (kind='poll' and jsonb_typeof(options)='array' and jsonb_array_length(options) between 2 and 4 and closes_at is not null)
 )
);
create table if not exists public.post_interactive_responses (
 post_id uuid not null references public.post_interactive(post_id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 option_index integer,
 answer text,
 created_at timestamptz not null default now(),
 primary key (post_id,user_id),
 constraint response_shape check ((option_index is not null and answer is null) or (option_index is null and answer is not null and char_length(btrim(answer)) between 1 and 500))
);
create index if not exists post_interactive_responses_post_idx on public.post_interactive_responses(post_id);
alter table public.post_interactive enable row level security;
alter table public.post_interactive_responses enable row level security;
drop policy if exists interactive_read on public.post_interactive;
create policy interactive_read on public.post_interactive for select to authenticated using (exists(select 1 from public.posts p where p.id=post_id));
drop policy if exists interactive_responses_read on public.post_interactive_responses;
create policy interactive_responses_read on public.post_interactive_responses for select to authenticated using (exists(select 1 from public.posts p where p.id=post_id));
-- Direct inserts are intentionally disabled. RPC validates post ownership and response conditions.
create or replace function public.create_interactive_post(p_content text,p_kind text,p_options text[] default null,p_hours integer default 24)
returns uuid language plpgsql security definer set search_path=public as $$
declare v_user uuid:=auth.uid();v_id uuid;v_options jsonb;
begin
 if v_user is null then raise exception 'Login required'; end if;
 if p_kind not in ('poll','question') then raise exception 'Invalid kind'; end if;
 if char_length(btrim(coalesce(p_content,''))) not between 1 and 500 then raise exception 'Content must be 1-500 characters'; end if;
 if p_kind='poll' then
  if coalesce(array_length(p_options,1),0) not between 2 and 4 or p_hours not in (1,6,24,72,168) then raise exception 'Invalid poll settings'; end if;
  if exists(select 1 from unnest(p_options) v where char_length(btrim(coalesce(v,''))) not between 1 and 80) then raise exception 'Invalid option'; end if;
  if (select count(distinct lower(btrim(v))) from unnest(p_options) v) <> array_length(p_options,1) then raise exception 'Duplicate options'; end if;
  v_options:=to_jsonb(array(select btrim(v) from unnest(p_options) v));
 else v_options:='[]'::jsonb;
 end if;
 insert into public.posts(user_id,content,post_type,result_type,result_id) values(v_user,btrim(p_content),'normal',null,null) returning id into v_id;
 insert into public.post_interactive(post_id,kind,options,closes_at) values(v_id,p_kind,v_options,case when p_kind='poll' then now()+make_interval(hours=>p_hours) else null end);
 return v_id;
end;$$;
create or replace function public.submit_interactive_response(p_post_id uuid,p_option_index integer default null,p_answer text default null)
returns void language plpgsql security definer set search_path=public as $$
declare v_user uuid:=auth.uid();v_item public.post_interactive%rowtype;
begin
 if v_user is null then raise exception 'Login required'; end if;
 select * into v_item from public.post_interactive where post_id=p_post_id for share;
 if not found then raise exception 'Interactive post not found'; end if;
 if not exists(select 1 from public.posts where id=p_post_id) then raise exception 'Post not found'; end if;
 if v_item.kind='poll' then
  if v_item.closes_at<=now() then raise exception 'Poll closed'; end if;
  if p_option_index is null or p_option_index<0 or p_option_index>=jsonb_array_length(v_item.options) or p_answer is not null then raise exception 'Invalid vote'; end if;
 else
  if p_option_index is not null or char_length(btrim(coalesce(p_answer,''))) not between 1 and 500 then raise exception 'Invalid answer'; end if;
 end if;
 insert into public.post_interactive_responses(post_id,user_id,option_index,answer)
 values(p_post_id,v_user,p_option_index,case when v_item.kind='question' then btrim(p_answer) else null end);
end;$$;
revoke all on function public.create_interactive_post(text,text,text[],integer) from public;
revoke all on function public.submit_interactive_response(uuid,integer,text) from public;
grant execute on function public.create_interactive_post(text,text,text[],integer) to authenticated;
grant execute on function public.submit_interactive_response(uuid,integer,text) to authenticated;
-- Anonymous public results; individual respondent IDs are never exposed.
drop policy if exists interactive_responses_read on public.post_interactive_responses;
create policy interactive_responses_own_read on public.post_interactive_responses
for select to authenticated using (user_id = (select auth.uid()));

create or replace function public.get_interactive_results(p_post_ids uuid[])
returns table(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean)
language sql stable security definer set search_path = '' as $$
 select i.post_id,
   (select count(*) from public.post_interactive_responses r where r.post_id=i.post_id),
   (select coalesce(jsonb_object_agg(t.option_index::text,t.cnt),'{}'::jsonb)
      from (select r.option_index,count(*) cnt from public.post_interactive_responses r
            where r.post_id=i.post_id and r.option_index is not null group by r.option_index) t),
   (select coalesce(jsonb_agg(jsonb_build_object('answer',r.answer,'created_at',r.created_at) order by r.created_at),'[]'::jsonb)
      from public.post_interactive_responses r where r.post_id=i.post_id and r.answer is not null),
   (select r.option_index from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid())),
   exists(select 1 from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid()))
 from public.post_interactive i
 where i.post_id=any(p_post_ids)
   and (select auth.uid()) is not null
   and exists(select 1 from public.posts p where p.id=i.post_id);
$$;
revoke all on function public.get_interactive_results(uuid[]) from public;
grant execute on function public.get_interactive_results(uuid[]) to authenticated;
-- Required grants for interactive feed queries; writes remain RPC-only.
revoke all on table public.post_interactive, public.post_interactive_responses from anon, authenticated;
grant select on table public.post_interactive, public.post_interactive_responses to authenticated;
-- Do not expose answer timestamps: they can be correlated with user activity.
create or replace function public.get_interactive_results(p_post_ids uuid[])
returns table(post_id uuid, total_votes bigint, vote_counts jsonb, answers jsonb, my_option_index integer, has_responded boolean)
language sql stable security definer set search_path = '' as $$
 select i.post_id,
   (select count(*) from public.post_interactive_responses r where r.post_id=i.post_id),
   (select coalesce(jsonb_object_agg(t.option_index::text,t.cnt),'{}'::jsonb)
      from (select r.option_index,count(*) cnt from public.post_interactive_responses r
            where r.post_id=i.post_id and r.option_index is not null group by r.option_index) t),
   (select coalesce(jsonb_agg(jsonb_build_object('answer',r.answer) order by r.created_at),'[]'::jsonb)
      from public.post_interactive_responses r where r.post_id=i.post_id and r.answer is not null),
   (select r.option_index from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid())),
   exists(select 1 from public.post_interactive_responses r where r.post_id=i.post_id and r.user_id=(select auth.uid()))
 from public.post_interactive i
 where i.post_id=any(p_post_ids)
   and (select auth.uid()) is not null
   and exists(select 1 from public.posts p where p.id=i.post_id);
$$;
revoke all on function public.get_interactive_results(uuid[]) from public;
grant execute on function public.get_interactive_results(uuid[]) to authenticated;

-- Historical question data must survive both apply and feature-disable.
insert into public.posts(id,user_id,content,post_type) values('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000001','historical question fixture','normal');
insert into public.post_interactive(post_id,kind,options) values('20000000-0000-0000-0000-000000000001','question','[]');
insert into public.post_interactive_responses(post_id,user_id,answer) values('20000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000002','historical answer fixture');

-- Simulate a permissive OR policy left by an old deployment. The restrictive
-- candidate must defeat it for every actor, not just rely on own-row filtering.
create policy legacy_response_read_fixture on public.post_interactive_responses for select to authenticated using(true);

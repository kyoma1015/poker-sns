-- ISOLATED TEST FIXTURE ONLY, not a reconstruction of production application DB.
\set ON_ERROR_STOP on
create extension if not exists pgcrypto;
do $$begin
 if to_regprocedure('auth.uid()') is null then raise exception 'Official Supabase auth.uid() missing: do not substitute plain Postgres'; end if;
end$$;
-- The official image owns auth.users; never create/replace Auth objects.
do $$begin
 if to_regclass('auth.users') is null then raise exception 'Official Supabase auth.users missing'; end if;
end$$;
insert into auth.users(id,email) values
 ('10000000-0000-0000-0000-000000000001','owner@fixture.invalid'),
 ('10000000-0000-0000-0000-000000000002','voter@fixture.invalid'),
 ('10000000-0000-0000-0000-000000000003','observer@fixture.invalid') on conflict (id) do nothing;
create table public.profiles(id uuid primary key references auth.users,display_name text,poker_id text,avatar_url text);
insert into public.profiles values
 ('10000000-0000-0000-0000-000000000001','Fixture Owner','fixture_owner',null),
 ('10000000-0000-0000-0000-000000000002','Fixture Voter','fixture_voter',null),
 ('10000000-0000-0000-0000-000000000003','Fixture Observer','fixture_observer',null);
create table public.posts(id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users,content text not null,post_type text not null default 'normal',result_type text,result_id uuid,created_at timestamptz not null default now());
create table public.user_blocks(blocker_id uuid references auth.users,blocked_id uuid references auth.users,primary key(blocker_id,blocked_id));
create table public.notifications(id uuid primary key default gen_random_uuid(),user_id uuid not null references auth.users,actor_id uuid not null references auth.users,type text not null,post_id uuid references public.posts,read_at timestamptz,created_at timestamptz not null default now(),event_key text unique);
alter table public.posts enable row level security;
alter table public.profiles enable row level security;
alter table public.user_blocks enable row level security;
alter table public.notifications enable row level security;
create policy posts_read on public.posts for select to authenticated using(true);
create policy profiles_read on public.profiles for select to authenticated using(true);
create policy blocks_read on public.user_blocks for select to authenticated using(blocker_id=auth.uid() or blocked_id=auth.uid());
create policy notifications_own_read on public.notifications for select to authenticated using(user_id=auth.uid());
-- Deliberately unsafe old-client grant/policy. The candidate MUST preserve the
-- INSERT grant while preventing poll_closed forgery despite this permissive OR.
create policy legacy_notification_insert on public.notifications for insert to authenticated with check(true);
create policy notifications_own_update on public.notifications for update to authenticated using(user_id=auth.uid()) with check(user_id=auth.uid());
grant usage on schema public to anon,authenticated;
grant select on public.posts,public.profiles,public.user_blocks,public.notifications to authenticated;
grant insert,update on public.notifications to authenticated;
create function public.legacy_notification_insert_fixture(p_user_id uuid,p_actor_id uuid,p_type text,p_post_id uuid) returns void
language sql security definer set search_path='' as $$insert into public.notifications(user_id,actor_id,type,post_id) values(p_user_id,p_actor_id,p_type,p_post_id)$$;
revoke all on function public.legacy_notification_insert_fixture(uuid,uuid,text,uuid) from public,anon;
grant execute on function public.legacy_notification_insert_fixture(uuid,uuid,text,uuid) to authenticated;
-- Local-only authenticator for PostgREST; not a production credential.
alter role authenticator password 'poll-fixture-only-password';
grant anon,authenticated to authenticator;

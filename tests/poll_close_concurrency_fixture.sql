\set ON_ERROR_STOP on
create extension if not exists pgcrypto;
create role anon nologin;
create role authenticated nologin;
create schema poll_private;
create table public.posts(id uuid primary key,user_id uuid not null);
create table public.post_interactive(post_id uuid primary key references public.posts(id),kind text not null,closes_at timestamptz not null);
create table poll_private.close_receipts(post_id uuid primary key references public.post_interactive(post_id),notification_id uuid unique not null,created_at timestamptz default now());
create table public.notifications(id uuid primary key,user_id uuid not null,actor_id uuid not null,type text not null,post_id uuid not null,event_key text unique);
alter table public.notifications enable row level security;
create table public.synthetic_controls(fail boolean not null default false, delay_seconds integer not null default 0);
insert into public.synthetic_controls values(false,0);
create or replace function public.synthetic_notify_guard() returns trigger language plpgsql as $$
declare v_fail boolean; v_delay integer;
begin
 select fail,delay_seconds into v_fail,v_delay from public.synthetic_controls limit 1;
 if v_delay>0 then perform pg_sleep(v_delay); end if;
 if v_fail then raise exception 'synthetic notification insert failure'; end if;
 return new;
end $$;
create trigger synthetic_notify_guard before insert on public.notifications for each row execute function public.synthetic_notify_guard();
create table public.synthetic_ids(label text primary key,id uuid unique not null,owner_id uuid not null);
insert into public.synthetic_ids values
('one','10000000-0000-4000-8000-000000000001','20000000-0000-4000-8000-000000000001'),
('two','10000000-0000-4000-8000-000000000002','20000000-0000-4000-8000-000000000002'),
('legacy','10000000-0000-4000-8000-000000000003','20000000-0000-4000-8000-000000000003');
insert into public.posts select id,owner_id from public.synthetic_ids;
insert into public.post_interactive select id,'poll',clock_timestamp()-interval '1 hour' from public.synthetic_ids;
insert into public.notifications(id,user_id,actor_id,type,post_id,event_key)
select gen_random_uuid(),owner_id,owner_id,'poll_closed',id,'poll_closed:'||id from public.synthetic_ids where label='legacy';

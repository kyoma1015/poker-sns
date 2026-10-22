\set ON_ERROR_STOP on
create extension if not exists pg_cron;
create schema if not exists poll_private;
create schema if not exists poll_fixture;
create table poll_fixture.events(kind text not null);
create table poll_fixture.votes(id integer primary key, voter text not null);
insert into poll_fixture.votes values (1,'synthetic-a'),(2,'synthetic-b');
create table poll_fixture.receipts(poll_id int primary key, created_at timestamptz default now());
create role anon nologin;
create role authenticated nologin;
create or replace function public.get_interactive_results_v4() returns int language sql as 'select 1';
grant execute on function public.get_interactive_results_v4() to public,anon,authenticated;
create or replace function poll_private.close_due_polls() returns void language plpgsql as $$
begin
 insert into poll_fixture.receipts(poll_id) values(1) on conflict do nothing;
end $$;
create or replace function public.poll_synthetic_legacy() returns void language plpgsql as $$
begin
 perform pg_sleep(12);
 insert into poll_fixture.receipts(poll_id) values(1) on conflict do nothing;
end $$;
select cron.schedule('poker_id_poll_closed_notifications','5 seconds','select public.poll_synthetic_legacy();');

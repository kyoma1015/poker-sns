-- Poker ID card theme / publication settings
-- Execute once in Supabase SQL Editor before testing card publication.
create table if not exists public.poker_id_cards (
  user_id uuid primary key references auth.users(id) on delete cascade,
  theme text not null default 'classic',
  is_public boolean not null default false,
  updated_at timestamptz not null default now(),
  constraint poker_id_cards_theme_check check (
    theme in ('classic','ice','navy','mint','sage','lavender','blossom','cream')
  )
);
alter table public.poker_id_cards enable row level security;
drop policy if exists "poker_id_cards_select" on public.poker_id_cards;
create policy "poker_id_cards_select" on public.poker_id_cards
  for select to authenticated using (auth.uid() = user_id or is_public = true);
drop policy if exists "poker_id_cards_insert" on public.poker_id_cards;
create policy "poker_id_cards_insert" on public.poker_id_cards
  for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists "poker_id_cards_update" on public.poker_id_cards;
create policy "poker_id_cards_update" on public.poker_id_cards
  for update to authenticated using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
-- No delete policy required. Existing profile, results and diagnosis RLS stay untouched.

-- SQL migrations run by the API may not inherit standard default grants.
grant select, insert, update on table public.poker_id_cards to authenticated;

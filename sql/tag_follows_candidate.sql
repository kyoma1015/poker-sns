-- REVIEW ONLY: do not apply to production without separate authorization.
-- Authenticated users may only manage their own followed tags.
create table if not exists public.tag_follows (
  user_id uuid not null references auth.users(id) on delete cascade,
  tag text not null check (length(tag) between 1 and 40 and tag = upper(btrim(tag)) and tag !~ '[[:space:]]'),
  created_at timestamptz not null default now(),
  primary key (user_id, tag)
);
alter table public.tag_follows enable row level security;
revoke all on public.tag_follows from anon;
grant select, insert, delete on public.tag_follows to authenticated;
drop policy if exists tag_follows_select_own on public.tag_follows;
create policy tag_follows_select_own on public.tag_follows for select to authenticated using (auth.uid() = user_id);
drop policy if exists tag_follows_insert_own on public.tag_follows;
create policy tag_follows_insert_own on public.tag_follows for insert to authenticated with check (auth.uid() = user_id);
drop policy if exists tag_follows_delete_own on public.tag_follows;
create policy tag_follows_delete_own on public.tag_follows for delete to authenticated using (auth.uid() = user_id);
-- Requires separate production schema/RLS review before execution.

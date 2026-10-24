-- ISOLATED SUPABASE LOCAL STACK ONLY. Never execute against production.
create table if not exists public.posts (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id),
 content text not null default '',
 created_at timestamptz not null default now(),
 image_urls text[] not null default '{}'
);
alter table public.posts enable row level security;
create policy video_qa_posts_owner_insert on public.posts for insert to authenticated
 with check ((select auth.uid()) = user_id);
create policy video_qa_posts_owner_select on public.posts for select to authenticated
 using ((select auth.uid()) = user_id);
grant select, insert on public.posts to authenticated;

-- Isolated visibility test policy; not a production authorization migration.
alter table public.posts add column if not exists is_public boolean not null default false;
create policy video_qa_posts_public_select on public.posts for select to authenticated
 using (is_public = true);

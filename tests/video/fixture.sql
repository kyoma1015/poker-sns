-- ISOLATED QA FIXTURE ONLY. Never execute against production.
\set ON_ERROR_STOP on
create extension if not exists pgcrypto;
create schema if not exists auth;
create schema if not exists storage;
create role video_owner nologin;
create role video_viewer nologin;
create table public.posts(id uuid primary key, user_id uuid not null, image_urls text[] not null default '{}');
create table storage.buckets(id text primary key, name text not null, public boolean not null,
 file_size_limit bigint, allowed_mime_types text[]);
create table storage.objects(id uuid primary key default gen_random_uuid(), bucket_id text references storage.buckets(id),
 name text not null, owner_id text);
create or replace function auth.uid() returns uuid language sql stable as $$
 select nullif(current_setting('request.jwt.claim.sub', true),'')::uuid $$;
create or replace function storage.foldername(p text) returns text[] language sql immutable as $$
 select (string_to_array(p, '/'))[1:array_length(string_to_array(p, '/'),1)-1] $$;
-- Only in disposable fixture: map authenticated to a real login role.
create role authenticated nologin;
grant authenticated to video_owner, video_viewer;
grant usage on schema storage,auth,public to authenticated;
grant select,insert,delete on storage.objects to authenticated;
grant select on storage.buckets to authenticated;
alter table storage.objects enable row level security;
alter table storage.objects force row level security;

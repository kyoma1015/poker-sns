-- ISOLATED FIXTURE ONLY. Official Supabase Auth migration, rendered Namespace=auth.
-- Upstream commit ce9a8eee0cc042be8c7a42981a7ddae631e41d91
-- Source migrations/20220224000811_update_auth_functions.up.sql
-- Original Git blob SHA-1 4be423739aa3bf07bc3769aea5cc7751959ad53e
-- The postgres image initializes pre-2022 Auth helpers; GoTrue normally upgrades
-- them. Our REST-only fixture applies this exact upstream migration explicitly.
-- update auth functions

create or replace function auth.uid() 
returns uuid 
language sql stable
as $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.sub', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub')
  )::uuid
$$;

create or replace function auth.role() 
returns text 
language sql stable
as $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.role', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'role')
  )::text
$$;

create or replace function auth.email() 
returns text 
language sql stable
as $$
  select 
  coalesce(
    nullif(current_setting('request.jwt.claim.email', true), ''),
    (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'email')
  )::text
$$;


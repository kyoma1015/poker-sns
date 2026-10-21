-- FRESH ISOLATED CONTAINER ONLY. The official image reserves authenticator;
-- configure its local fixture password as the image's legitimate admin.
\set ON_ERROR_STOP on
alter role authenticator password 'poll-fixture-only-password';
-- Official image already grants anon/authenticated; do not broaden membership.
do $$begin
 if not pg_has_role('authenticator','anon','MEMBER') or not pg_has_role('authenticator','authenticated','MEMBER') then
  raise exception 'Official authenticator role memberships missing';
 end if;
end$$;

#!/usr/bin/env bash
set -euo pipefail
# Called only for the fresh disposable container owned by run_dm_model.sh.
model_container="${1:?fresh model container required}"
[[ "$model_container" == abd-dm-model-* ]] || { echo 'BLOCKED: unknown container scope'; exit 2; }
sql() { timeout 60s docker exec -i "$model_container" psql -X -qAt -v ON_ERROR_STOP=1 -U postgres; }
catalog() {
 sql <<'SQL'
SELECT md5(jsonb_build_object(
 'table_acl',(SELECT relacl::text FROM pg_class WHERE oid='dm_model.messages'::regclass),
 'column_acls',(SELECT jsonb_agg(jsonb_build_array(attname,attacl::text) ORDER BY attnum) FROM pg_attribute WHERE attrelid='dm_model.messages'::regclass AND attnum>0),
 'policies',(SELECT jsonb_agg(jsonb_build_array(polname,polcmd,polroles::text,polpermissive,pg_get_expr(polqual,polrelid),pg_get_expr(polwithcheck,polrelid)) ORDER BY polname) FROM pg_policy WHERE polrelid='dm_model.messages'::regclass)
)::text);
SQL
}
log_file="$(mktemp)"
trap 'rm -f "$log_file"' EXIT
reject() {
 local scenario="$1" expected="$2" before after
 before="$(catalog)"
 if sql < tests/authorization/dm_policy_candidate.sql >"$log_file" 2>&1; then
   echo "FAIL:$scenario candidate silently accepted unreviewed authorization"; exit 1
 fi
 grep -q "$expected" "$log_file" || { cat "$log_file"; exit 1; }
 echo "PASS:${scenario}_refused"
 after="$(catalog)"
 test "$before" = "$after" || { echo "FAIL:$scenario catalog changed despite rejection"; exit 1; }
 echo "PASS:${scenario}_atomic_rollback"
}
sql <<'SQL'
CREATE ROLE model_legacy_writer NOLOGIN NOSUPERUSER NOBYPASSRLS;
GRANT UPDATE(content) ON dm_model.messages TO model_legacy_writer;
GRANT model_legacy_writer TO model_authenticated;
SQL
reject inherited_column_acl DM_UNEXPECTED_EFFECTIVE_PRIVILEGES
sql <<'SQL'
REVOKE model_legacy_writer FROM model_authenticated;
REVOKE UPDATE(content) ON dm_model.messages FROM model_legacy_writer;
DROP ROLE model_legacy_writer;
CREATE POLICY legacy_public_read ON dm_model.messages FOR SELECT TO PUBLIC USING(true);
SQL
reject extra_permissive_policy DM_UNREVIEWED_POLICY
sql <<'SQL'
DROP POLICY legacy_public_read ON dm_model.messages;
ALTER ROLE model_authenticated BYPASSRLS;
SQL
reject bypassrls_actor DM_UNSAFE_ACTOR_ROLE
sql <<'SQL'
ALTER ROLE model_authenticated NOBYPASSRLS;
SQL
echo 'DM_PREFLIGHT:6 PASS/0 FAIL; metadata unchanged after each refused proposal'

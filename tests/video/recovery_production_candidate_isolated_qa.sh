#!/usr/bin/env bash
# Disposable local Supabase only; never run against production.
set -euo pipefail
dburl="${1:?pass isolated DB_URL}"
case "$dburl" in
  *127.0.0.1:56322/*|*localhost:56322/*) ;;
  *) echo "REFUSE: recovery schema QA requires local isolated 56322" >&2; exit 2;;
esac
candidate=tests/video/recovery_production_candidate_NOT_APPROVED.sql
sql() { psql "$dburl" -X -v ON_ERROR_STOP=1 -q -c "$1"; }
apply() { psql "$dburl" -X -v ON_ERROR_STOP=1 -q -f "$candidate"; }
expect_reject() {
 local expected="$1" out
 out="$(mktemp)"
 if apply >"$out" 2>&1; then cat "$out"; rm -f "$out"; echo "FAIL: expected rejection $expected" >&2; exit 1; fi
 if ! grep -Fq "$expected" "$out"; then cat "$out"; rm -f "$out"; echo "FAIL: wrong SQL rejection" >&2; exit 1; fi
 rm -f "$out"
}
# Reapply against populated recovery state and prove no writes or data loss.
if [[ "${2:-install}" == recheck ]]; then
 before="$(psql "$dburl" -AtX -v ON_ERROR_STOP=1 -c "select (select count(*) from public.posts)::text || ':' || (select count(*) from video_private.recovery_manifests)::text || ':' || (select count(*) from video_private.consumed_nonces)::text")"
 apply
 after="$(psql "$dburl" -AtX -v ON_ERROR_STOP=1 -c "select (select count(*) from public.posts)::text || ':' || (select count(*) from video_private.recovery_manifests)::text || ':' || (select count(*) from video_private.consumed_nonces)::text")"
 [[ "$before" == "$after" ]] || { echo "FAIL: idempotent rerun modified posts/manifests/nonces" >&2; exit 1; }
 echo 'PASS: populated production-like schema reapply preserved posts/manifests/nonces'
 exit 0
fi
# Deliberately mutate a single function only AFTER real HTTP E2E completes.
# Verify migration refuses the drift and preserves all previously published rows.
if [[ "${2:-install}" == drift ]]; then
 before="$(psql "$dburl" -AtX -v ON_ERROR_STOP=1 -c "select (select count(*) from public.posts)::text || ':' || (select count(*) from video_private.recovery_manifests)::text || ':' || (select count(*) from video_private.consumed_nonces)::text")"
 sql "alter function public.video_recovery_state_v1(text) set search_path to public;"
 expect_reject 'function definition drift or missing migration seal'
 after="$(psql "$dburl" -AtX -v ON_ERROR_STOP=1 -c "select (select count(*) from public.posts)::text || ':' || (select count(*) from video_private.recovery_manifests)::text || ':' || (select count(*) from video_private.consumed_nonces)::text")"
 [[ "$before" == "$after" ]] || { echo "FAIL: drift rejection changed production-like rows" >&2; exit 1; }
 echo 'PASS: mutated function rejected and posts/manifests/nonces preserved'
 exit 0
fi
# The real database has this table; the disposable fixture's legacy bootstrap may not.
sql "create schema if not exists video_private;
create table if not exists video_private.general_public_rollout
 (singleton boolean primary key,enabled boolean not null);"
# Snapshot existing production-like API/Storage catalog before any migration DDL.
# This is a catalog fingerprint, not a substitute for a production approval.
baseline_catalog() {
 psql "$dburl" -AtX -v ON_ERROR_STOP=1 -c "
 select md5(
 pg_get_functiondef('public.video_publish_attested_v1(uuid,text,uuid,text,integer,text,bigint,text,text,smallint)'::regprocedure)
 || pg_get_functiondef('public.video_reserve_object_key(uuid,text)'::regprocedure)
 || coalesce((select string_agg(policyname || cmd || roles::text || coalesce(qual,'') || coalesce(with_check,''),'|' order by policyname)
              from pg_policies where schemaname='storage' and tablename='objects'),'')
 || coalesce((select string_agg(attname || format_type(atttypid,atttypmod),'|' order by attnum)
              from pg_attribute where attrelid='public.posts'::regclass and attnum>0 and not attisdropped),'')
 || coalesce((select string_agg(attname || format_type(atttypid,atttypmod),'|' order by attnum)
              from pg_attribute where attrelid='public.video_reserved_object_keys'::regclass and attnum>0 and not attisdropped),'')
 );"
}
baseline_before="$(baseline_catalog)"
# The disposable stack does not install the production rollout gate.
# Supply a LOCAL-ONLY gate shim for schema-contract validation. It is not
# evidence of the actual production gate implementation.
sql "create or replace function public.video_rollout_allowed()
 returns boolean language sql stable security invoker set search_path=''
 as \$\$ select true \$\$;"
# Deliberate incomplete prior migration MUST fail before writing any new RPC.
sql "create table video_private.recovery_manifests (object_path text);"
expect_reject 'preexisting unsealed migration objects'
sql "drop table video_private.recovery_manifests;"
echo 'PASS: incomplete migration rejected without overwriting'
# First application + identical reapplication.
apply
sql "do \$seal\$ begin
 if (select count(*) from video_private.recovery_migration_seal where version='recovery-v1') <> 1
 then raise exception 'missing recovery migration seal'; end if;
 end \$seal\$;"
apply
[[ "$baseline_before" == "$(baseline_catalog)" ]] || { echo "FAIL: preexisting parent RPC/Storage/post schema drifted" >&2; exit 1; }
echo 'PASS: existing parent RPCs, Storage policies and post/ledger columns unchanged'
echo 'PASS: production-like candidate SQL first and second application'
# Schema and grants must remain sealed, no expansion of permissions.
sql "do \$check\$ begin
 if not (select relrowsecurity from pg_class where oid='video_private.recovery_manifests'::regclass)
  or has_table_privilege('anon','video_private.recovery_manifests','SELECT')
  or has_table_privilege('authenticated','video_private.recovery_manifests','SELECT')
  or has_function_privilege('anon','public.video_recovery_state_v1(text)','EXECUTE')
  or not has_function_privilege('authenticated','public.video_recovery_state_v1(text)','EXECUTE')
 then raise exception 'recovery privilege invariant violation'; end if;
 end \$check\$;"
echo 'PASS: recovery manifest RLS and RPC grants preserved'
# Run the actual HTTP recovery E2E BEFORE the drift mutation below.

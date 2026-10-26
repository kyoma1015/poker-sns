#!/usr/bin/env bash
# Disposable local Supabase DB only. Exercises the exact review-candidate RPC body.
set -euo pipefail
dburl="${1:?disposable local DB URL required}"
[[ "$dburl" == *"127.0.0.1:56322"* ]] || { echo 'BLOCKED: non-local DB'; exit 2; }
candidate=tests/video/production_additive_candidate.sql
# Extract the function from the production candidate, not a hand-copied test implementation.
sed -n '/^create or replace function public.video_reserve_object_key(/,/^\$\$;$/p' "$candidate" | psql "$dburl" -v ON_ERROR_STOP=1 >/dev/null
owner='11111111-1111-4111-8111-111111111111'
other='22222222-2222-4222-8222-222222222222'
# Parallel independent sessions, each with the same authenticated owner claim.
dir="$(mktemp -d)"
trap 'rm -rf "$dir"' EXIT
for i in $(seq 1 20); do
 (
  psql "$dburl" -v ON_ERROR_STOP=1 -Atqc "select set_config('request.jwt.claim.sub','$owner',false); select public.video_reserve_object_key('$owner', '$owner/$(printf '%08d' "$i")-1111-4111-8111-111111111111.webm');" >"$dir/$i.out" 2>"$dir/$i.err"
 ) &
done
wait || true
count="$(psql "$dburl" -Atqc "select count(*) from public.video_reserved_object_keys where owner_id='$owner' and created_at>now()-interval '1 hour'")"
[[ "$count" == 12 ]] || { echo "FAIL: concurrent hourly quota count=$count"; exit 1; }
echo 'PASS: 20 parallel reservations limited to 12'
# Distinct owner has a separate quota.
psql "$dburl" -v ON_ERROR_STOP=1 -Atqc "select set_config('request.jwt.claim.sub','$other',false); select public.video_reserve_object_key('$other','$other/00000001-1111-4111-8111-111111111111.webm');" >/dev/null
# Shift first owner's reservations out of hourly window, then seed 68 more
# within 24h (total 80); no privileged client-facing mutation is tested.
psql "$dburl" -v ON_ERROR_STOP=1 -c "update public.video_reserved_object_keys set created_at=now()-interval '2 hours' where owner_id='$owner';" >/dev/null
psql "$dburl" -v ON_ERROR_STOP=1 -c "insert into public.video_reserved_object_keys(bucket_id,object_path,owner_id,created_at) select 'post-videos','$owner/'||lpad(n::text,8,'0')||'-2222-4222-8222-222222222222.webm','$owner',now()-interval '2 hours' from generate_series(1,68) n;" >/dev/null
if psql "$dburl" -v ON_ERROR_STOP=1 -Atqc "select set_config('request.jwt.claim.sub','$owner',false); select public.video_reserve_object_key('$owner','$owner/99999999-1111-4111-8111-111111111111.webm');" >"$dir/over.out" 2>"$dir/over.err"; then
 echo 'FAIL: 24-hour quota accepted 81st reservation'; exit 1
fi
grep -q 'video reservation rate limit exceeded' "$dir/over.err" || { cat "$dir/over.err"; exit 1; }
echo 'PASS: 24-hour quota rejects 81st; independent owner accepted'

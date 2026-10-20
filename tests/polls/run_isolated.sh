#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
# Always target the managed LOCAL daemon; never an inherited remote Docker host.
unset DOCKER_HOST DOCKER_CONTEXT DOCKER_TLS DOCKER_TLS_VERIFY DOCKER_CERT_PATH
export DOCKER_HOST=unix:///var/run/docker.sock
# Refuse a collision BEFORE installing any cleanup trap: never remove a prior
# developer/agent's containers, network, volume or test data.
for qa_container in pokerid-poll-qa-db pokerid-poll-qa-rest; do
  if docker inspect "$qa_container" >/dev/null 2>&1; then
    echo "BLOCKED: existing $qa_container; no automatic deletion" >&2
    exit 2
  fi
done
if docker network inspect pokerid-poll-isolated_default >/dev/null 2>&1; then
  echo "BLOCKED: existing test project network; no automatic deletion" >&2
  exit 2
fi
export POLL_QA_RUN_ID="poll-qa-$(date +%s)-$$"
qa_compose=(docker compose -f tests/polls/docker-compose.yml)
mkdir -p docs/qa/issue22-polls-20261020
cleanup() {
  qa_exit=$?
  "${qa_compose[@]}" logs --no-color > docs/qa/issue22-polls-20261020/docker.log 2>&1 || true
  if [ "$qa_exit" -ne 0 ]; then tail -n 100 docs/qa/issue22-polls-20261020/docker.log >&2; fi
  for qa_container in pokerid-poll-qa-db pokerid-poll-qa-rest; do
    if docker inspect "$qa_container" >/dev/null 2>&1; then
      qa_owner=$(docker inspect --format '{{index .Config.Labels "pokerid.qa.run-id"}}' "$qa_container")
      if [ "$qa_owner" != "$POLL_QA_RUN_ID" ]; then
        echo "BLOCKED cleanup: resource ownership changed" >&2
        return
      fi
    fi
  done
  "${qa_compose[@]}" down --volumes
}
trap cleanup EXIT
"${qa_compose[@]}" up -d --wait db
for sql_file in tests/polls/bootstrap_fixture.sql tests/polls/legacy_schema_fixture.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
# Fresh fixture has a preserved question. Add a TEST-ONLY old poll with an
# unknown privacy mode and prove the candidate fails transactionally.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
insert into public.posts(id,user_id,content) values('20000000-0000-0000-0000-000000000099','10000000-0000-0000-0000-000000000001','unknown privacy fixture');
insert into public.post_interactive(post_id,kind,options,closes_at) values('20000000-0000-0000-0000-000000000099','poll','["A","B"]',now()+interval '1 hour');
SQL
if docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < sql/poll_only/forward_candidate.sql > docs/qa/issue22-polls-20261020/unknown-privacy-guard.log 2>&1; then
  echo "FAIL: unknown historical privacy was accepted" >&2
  exit 1
fi
grep -q 'unknown historical privacy' docs/qa/issue22-polls-20261020/unknown-privacy-guard.log
# This deletes only the two synthetic rows inserted just above, never original
# question rows or any developer database. The whole database is a fresh fixture.
docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 <<'SQL'
do $$begin
 if exists(select 1 from information_schema.columns where table_schema='public' and table_name='post_interactive' and column_name='is_anonymous') then raise exception 'Failed guard left partial DDL'; end if;
end$$;
delete from public.posts where id='20000000-0000-0000-0000-000000000099';
SQL
for sql_file in sql/poll_only/forward_candidate.sql sql/poll_only/forward_candidate.sql sql/poll_only/schedule_candidate.sql; do
  docker exec -i pokerid-poll-qa-db psql -U postgres -d postgres -v ON_ERROR_STOP=1 < "$sql_file"
done
"${qa_compose[@]}" up -d --wait rest
python tests/polls/verify_isolated.py

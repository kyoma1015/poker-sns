#!/usr/bin/env bash
# Disposable PG17/libpq regression, synthetic credentials only; no Supabase access.
set -euo pipefail
umask 077
tmp="$(mktemp -d)"
name="video-jit-readonly-$RANDOM-$$"
cleanup() {
  docker rm -f "$name" >/dev/null 2>&1 || true
  rm -rf -- "$tmp"
}
trap cleanup EXIT
mkdir "$tmp/tls"
# Synthetic self-signed TLS fixture, never a production key or certificate.
openssl req -x509 -newkey rsa:2048 -nodes -days 1 -subj '/CN=localhost' \
  -keyout "$tmp/tls/server.key" -out "$tmp/tls/server.crt" >/dev/null 2>&1
docker run -d --rm --network none --name "$name" \
  -e POSTGRES_PASSWORD=synthetic-ci-only -v "$tmp/tls:/tls:ro" postgres:17 \
  sh -ec 'cp /tls/server.key /tmp/server.key; cp /tls/server.crt /tmp/server.crt;
    chown postgres:postgres /tmp/server.key /tmp/server.crt; chmod 600 /tmp/server.key;
    exec docker-entrypoint.sh postgres -c ssl=on -c ssl_key_file=/tmp/server.key -c ssl_cert_file=/tmp/server.crt' >/dev/null
for i in $(seq 1 60); do
  if docker exec "$name" pg_isready -U postgres >/dev/null 2>&1; then break; fi
  sleep 1
done
docker exec "$name" pg_isready -U postgres >/dev/null
docker exec -i "$name" psql -U postgres -v ON_ERROR_STOP=1 -d postgres <<'SQL' >/dev/null
CREATE ROLE supabase_read_only_user LOGIN BYPASSRLS PASSWORD 'synthetic-ci-only';
GRANT pg_read_all_data TO supabase_read_only_user;
CREATE TABLE public.fixture(id integer PRIMARY KEY);
INSERT INTO public.fixture VALUES (1);
-- Intentionally grant write capability in this disposable negative fixture:
-- the session read-only guard must reject it despite the underlying privilege.
GRANT INSERT, DELETE ON public.fixture TO supabase_read_only_user;
ALTER ROLE supabase_read_only_user SET default_transaction_read_only = off;
ALTER ROLE supabase_read_only_user SET jit = off;
SQL
# Reproduce the old bug using a local-only URI. URI options win over PGOPTIONS.
old_state="$(docker exec -e PGPASSWORD=synthetic-ci-only \
  -e PGOPTIONS='-c default_transaction_read_only=on' "$name" \
  psql 'postgresql://supabase_read_only_user@127.0.0.1:5432/postgres?sslmode=require&options=-c%20jit%3Dtrue' \
  -X -At -v ON_ERROR_STOP=1 -c 'SHOW default_transaction_read_only')"
[[ "$old_state" == off ]] || { echo 'URI precedence negative control did not reproduce'; exit 1; }
# Run the same URL -> private env-file conversion as the real manual workflow.
python3 - "$tmp/libpq.env" <<'PY'
import importlib.util
import sys
from pathlib import Path
p = Path('scripts/video_backup_preflight.py')
spec = importlib.util.spec_from_file_location('backup_preflight', p)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
settings = {
    'PROD_DB_URL': f'postgresql://supabase_read_only_user.{module.PROJECT}:synthetic-ci-only@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require&options=-c%20jit%3Dtrue',
    'PROD_SUPABASE_URL': f'https://{module.PROJECT}.supabase.co',
    'PROD_STORAGE_READ_KEY': 'sb_secret_' + 'a'*32,
    'BACKUP_AGE_RECIPIENT': 'age1' + 'q'*58,
}
module.write_libpq_environment(settings, sys.argv[1])
PY
# Only this fixture substitutes the loopback host/user; no published port or
# outbound network. Production Workflow has no connection override switches.
docker run --rm --network "container:$name" --env-file "$tmp/libpq.env" \
  -e PGHOST=127.0.0.1 -e PGUSER=supabase_read_only_user postgres:17 sh -ec '
    state=$(psql -X -At -v ON_ERROR_STOP=1 -c "SELECT current_user || chr(124) || current_setting('\''jit'\'') || chr(124) || current_setting('\''default_transaction_read_only'\'') || chr(124) || current_setting('\''transaction_read_only'\'') || chr(124) || (SELECT ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid())")
    test "$state" = "supabase_read_only_user|on|on|on|true"
    for sql in "INSERT INTO public.fixture VALUES (2)" "DELETE FROM public.fixture"; do
      if psql -X -v ON_ERROR_STOP=1 -c "$sql" >/tmp/write.stdout 2>/tmp/write.stderr; then
        echo "Write unexpectedly succeeded" >&2; exit 1
      fi
      grep -q "read-only transaction" /tmp/write.stderr
    done
    pg_dump --format=custom -f /tmp/fixture.dump
    pg_restore --list /tmp/fixture.dump > /tmp/fixture.toc
    test -s /tmp/fixture.toc
    pg_dumpall --globals-only --no-role-passwords -f /tmp/globals.sql
    test -s /tmp/globals.sql
    test "$(psql -X -At -v ON_ERROR_STOP=1 -c "SELECT count(*) FROM public.fixture")" = 1
  '
echo 'PASS: old URI override reproduced; fixed JIT + read-only + TLS; INSERT/DELETE rejected; pg_dump and globals export succeeded; row retained'
echo 'LIMITATION: local PostgreSQL/libpq regression only, not live Supabase JIT or production backup/restore proof'

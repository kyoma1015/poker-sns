#!/usr/bin/env python3
"""Validate the approved production backup connection without exporting data."""
import os
import subprocess
from urllib.parse import parse_qs, unquote, urlsplit

PROJECT = "ephptepeuespnxtzdqby"
ROLE = "supabase_read_only_user"


def environment(raw):
    url = urlsplit(raw)
    options = parse_qs(url.query, strict_parsing=True, keep_blank_values=True)
    host = url.hostname or ""
    user = unquote(url.username or "")
    direct = host == f"db.{PROJECT}.supabase.co" and user == ROLE
    pooler = host.endswith(".pooler.supabase.com") and user == f"{ROLE}.{PROJECT}"
    if (url.scheme not in ("postgres", "postgresql") or not (direct or pooler)
            or url.port != 5432 or url.path != "/postgres" or url.fragment):
        raise ValueError("unexpected database origin")
    if set(options) - {"sslmode", "options", "connect_timeout"}:
        raise ValueError("unexpected connection option")
    if options.get("sslmode") not in (["require"], ["verify-full"]):
        raise ValueError("unexpected TLS option")
    jit = options.get("options")
    if jit is not None and not (pooler and jit == ["-c jit=true"]):
        raise ValueError("unexpected JIT option")
    if options.get("connect_timeout", ["15"]) not in (["5"], ["10"], ["15"], ["30"]):
        raise ValueError("unexpected timeout")
    password = unquote(url.password or "")
    if not password or any(ord(c) < 32 or ord(c) == 127 for c in password):
        raise ValueError("invalid credential format")
    return {
        "PGHOST": host, "PGPORT": "5432", "PGUSER": user, "PGDATABASE": "postgres",
        "PGPASSWORD": password, "PGSSLMODE": "verify-full", "PGSSLROOTCERT": "system",
        "PGCONNECT_TIMEOUT": "15", "PGGSSENCMODE": "disable", "PGTARGETSESSIONATTRS": "any",
        "PGOPTIONS": ("-c jit=true " if jit else "") + "-c default_transaction_read_only=on",
    }


def client(env, *args):
    return subprocess.run(
        ["docker", "run", "--rm", *[argument for key in env for argument in ("-e", key)],
         "postgres:17", *args],
        env={**os.environ, **env}, check=True, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL, timeout=120,
    ).stdout


def main():
    stage = "CONNECTION_CONFIG"
    try:
        env = environment(os.environ.pop("PROD_DB_URL"))
        stage = "CONNECT_TLS"
        sql = ("psql", "-XAt", "-v", "ON_ERROR_STOP=1", "-c")
        if client(env, *sql, "SELECT 1").strip() != b"1":
            raise ValueError("TLS probe failed")
        print("PASS: CONNECT_TLS")
        stage = "ROLE_READONLY"
        statement = """SELECT current_user='supabase_read_only_user'
          AND current_setting('default_transaction_read_only')='on'
          AND current_setting('transaction_read_only')='on'"""
        if client(env, *sql, statement).strip() != b"t":
            raise ValueError("unexpected session state")
        print("PASS: ROLE_READONLY")
        stage = "DUMP_PRIVILEGES"
        statement = """SELECT NOT EXISTS (
            SELECT FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname NOT IN ('pg_catalog','information_schema')
              AND n.nspname NOT LIKE 'pg_toast%' AND n.nspname NOT LIKE 'pg_temp_%'
              AND ((c.relkind IN ('r','p','m') AND
                    (NOT has_table_privilege(c.oid,'SELECT') OR row_security_active(c.oid)))
                OR (c.relkind='S' AND NOT has_sequence_privilege(c.oid,'SELECT')))
          )"""
        if client(env, *sql, statement).strip() != b"t":
            raise ValueError("incomplete table access")
        # Exercise pg_dump's catalog access and relation locks without retaining output.
        client(env, "pg_dump", "--schema-only", "--lock-wait-timeout=5s", "--file=/dev/null")
        print("PASS: DUMP_PRIVILEGES")
    except (KeyError, ValueError, OSError, subprocess.SubprocessError):
        raise SystemExit("FAIL: " + stage) from None


if __name__ == "__main__":
    main()

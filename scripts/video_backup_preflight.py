#!/usr/bin/env python3
"""Offline fail-closed validation before privileged backup connections. Logs no secrets."""
import os
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

PROJECT = "ephptepeuespnxtzdqby"
AGE_RECIPIENT = re.compile(r"age1[023456789acdefghjklmnpqrstuvwxyz]{58}\Z")

def validate(settings):
    required = ("PROD_DB_URL", "PROD_SUPABASE_URL", "PROD_STORAGE_READ_KEY", "BACKUP_AGE_RECIPIENT")
    if any(not settings.get(key) for key in required):
        raise ValueError("Missing required backup configuration")
    if settings["PROD_SUPABASE_URL"] != f"https://{PROJECT}.supabase.co":
        raise ValueError("Storage origin is not the approved production project")
    key = settings["PROD_STORAGE_READ_KEY"]
    if not (key.startswith("sb_secret_") or (key.count(".") == 2 and not key.startswith("sb_"))):
        raise ValueError("Unsupported Storage credential")
    if not AGE_RECIPIENT.fullmatch(settings["BACKUP_AGE_RECIPIENT"]):
        raise ValueError("Invalid age encryption recipient")
    try:
        url = urlsplit(settings["PROD_DB_URL"])
        query = parse_qs(url.query, keep_blank_values=True, strict_parsing=True)
        port = url.port
        host = url.hostname or ""
    except (ValueError, TypeError) as e:
        raise ValueError("Invalid PostgreSQL connection URL") from e
    if url.scheme not in ("postgres", "postgresql") or not url.username or not url.password or not port:
        raise ValueError("Missing PostgreSQL username, password, or port")
    if url.fragment or not url.path or url.path == "/":
        raise ValueError("Missing database name or unexpected URL fragment")
    expected_host = f"db.{PROJECT}.supabase.co"
    # Supabase session pooler host varies; verify official project suffix + username binding.
    direct = host == expected_host and port == 5432
    pooler = (host.endswith(".pooler.supabase.com")
              and host != ".pooler.supabase.com"
              and port == 5432 and url.username.endswith("." + PROJECT))
    if not (direct or pooler):
        raise ValueError("Unapproved PostgreSQL host, port or project role")
    if query.get("sslmode") not in (["require"], ["verify-full"]):
        raise ValueError("TLS must be enforced in exact sslmode parameter")
    if len(query.get("sslmode", [])) != 1:
        raise ValueError("Duplicate TLS setting")
    # Do not accept additional duplicate values or options that disable TLS or reroute DB.
    if any(len(values) != 1 for values in query.values()):
        raise ValueError("Ambiguous repeated PostgreSQL URL parameters")
    if any(param not in ("sslmode", "options", "connect_timeout") for param in query):
        raise ValueError("Unapproved PostgreSQL connection option")
    if "options" in query and (not pooler or query["options"] != ["-c jit=true"]):
        raise ValueError("Unapproved JIT libpq options")
    if "connect_timeout" in query and query["connect_timeout"] not in (["5"], ["10"], ["15"], ["30"]):
        raise ValueError("Unapproved database connection timeout")
    return True


def libpq_environment(settings):
    """Keep URI options from overriding read-only settings on any dump connection.

    Return an explicit Docker/libpq environment, never a rewritten secret URL.
    PGDATABASE is fixed so libpq cannot expand it as a second connection string.
    """
    validate(settings)
    url = urlsplit(settings["PROD_DB_URL"])
    query = parse_qs(url.query, keep_blank_values=True, strict_parsing=True)
    user = unquote(url.username)
    expected_user = "supabase_read_only_user"
    if url.hostname != f"db.{PROJECT}.supabase.co":
        expected_user += "." + PROJECT
    if user != expected_user or unquote(url.path) != "/postgres":
        raise ValueError("Backup requires the approved read-only role and database")
    options = "-c default_transaction_read_only=on"
    if "options" in query:
        options = "-c jit=true " + options
    result = {
        "PGHOST": url.hostname,
        "PGPORT": str(url.port),
        "PGUSER": user,
        "PGPASSWORD": unquote(url.password),
        "PGDATABASE": "postgres",
        "PGSSLMODE": query["sslmode"][0],
        "PGCONNECT_TIMEOUT": query.get("connect_timeout", ["15"])[0],
        "PGOPTIONS": options,
    }
    # Docker env files have no quoting/escaping: reject control characters before
    # creating the file, rather than allowing a password to inject another key.
    if any(not value or any(ord(c) < 32 or ord(c) == 127 for c in value)
           for value in result.values()):
        raise ValueError("Unsafe libpq environment value")
    return result


def write_libpq_environment(settings, destination):
    values = libpq_environment(settings)
    path = Path(destination)
    if path.parent.stat().st_mode & 0o077:
        raise ValueError("Connection file requires a private parent directory")
    # Never overwrite an existing credential file or follow a destination symlink.
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--write-libpq-env":
            write_libpq_environment(os.environ, sys.argv[2])
        elif len(sys.argv) == 1:
            validate(os.environ)
        else:
            raise ValueError("Unsupported preflight invocation")
        print("PASS: backup preflight configuration and origin validation (offline)")
    except Exception as exc:
        print("FAIL: backup preflight:", type(exc).__name__)
        raise SystemExit(2)


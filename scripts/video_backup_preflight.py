#!/usr/bin/env python3
"""Offline fail-closed validation before privileged backup connections. Logs no secrets."""
import os
import re
from urllib.parse import parse_qs, urlsplit

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
    if any(param in query for param in ("host", "hostaddr", "service", "sslrootcert", "passfile")):
        raise ValueError("Unsupported connection routing or credential overrides")
    return True

if __name__ == "__main__":
    try:
        validate(os.environ)
        print("PASS: backup preflight configuration and origin validation (offline)")
    except Exception as exc:
        print("FAIL: backup preflight:", type(exc).__name__)
        raise SystemExit(2)

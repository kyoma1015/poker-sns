#!/usr/bin/env python3
"""Credential-free Actions runner diagnosis; never authenticates to Postgres."""
import errno
import json
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import urllib.request

HOST = "db.ephptepeuespnxtzdqby.supabase.co"
PORT = 5432
CA_URL = "https://supabase-downloads.s3-ap-southeast-1.amazonaws.com/prod/ssl/prod-ca-2021.crt"


def diagnose():
    result = {
        "target": HOST,
        "port": PORT,
        "runner_ipv6_supported": socket.has_ipv6,
        "ipv6_default_route": False,
        "ipv6_dns_records": 0,
        "ipv6_tcp_reachable": False,
        "tls_hostname_verified": False,
        "credentials_loaded": False,
        "authentication_attempted": False,
        "database_query_sent": False,
    }
    try:
        route_command = (["ip", "-6", "route", "show", "default"]
                         if shutil.which("ip") else ["netstat", "-rn", "-f", "inet6"])
        route = subprocess.run(route_command,
                               capture_output=True, text=True, timeout=5, check=False)
        result["ipv6_default_route"] = route.returncode == 0 and any(
            line.split() and line.split()[0] == "default" for line in route.stdout.splitlines())
        addresses = socket.getaddrinfo(HOST, PORT, socket.AF_INET6, socket.SOCK_STREAM)
        addresses = list(dict.fromkeys(row[4] for row in addresses))
        result["ipv6_dns_records"] = len(addresses)
        if not addresses:
            result["status"] = "BLOCKED_NO_IPV6_DNS"
            return result
        # One bounded connection only. No IPv4 fallback, tunnels, network
        # modifications, credentials, StartupMessage, query or auth response.
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as connection:
            connection.settimeout(8)
            connection.connect(addresses[0])
            result["ipv6_tcp_reachable"] = True
            connection.sendall(struct.pack("!II", 8, 80877103))  # SSLRequest only
            if connection.recv(1) != b"S":
                result["status"] = "BLOCKED_SSL_NOT_SUPPORTED"
                return result
            with urllib.request.urlopen(CA_URL, timeout=10) as response:
                certificate = response.read(65537)
            if len(certificate) > 65536:
                raise ValueError("Unexpected certificate size")
            context = ssl.create_default_context(cadata=certificate.decode("ascii"))
            with context.wrap_socket(connection, server_hostname=HOST):
                result["tls_hostname_verified"] = True
        result["status"] = "IPV6_AND_TLS_REACHABLE_NO_AUTH_TESTED"
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result["status"] = "BLOCKED_CONNECTIVITY_OR_TLS"
        result["error_type"] = type(exc).__name__
        result["error_code"] = errno.errorcode.get(getattr(exc, "errno", None), "UNSPECIFIED")
    return result


if __name__ == "__main__":
    outcome = diagnose()
    print(json.dumps(outcome, sort_keys=True))
    sys.exit(0 if outcome["tls_hostname_verified"] else 2)

"""Supabase Auth-backed JWT validation adapter (not deployed).

Supabase Auth /user verifies the JWT signature and expiry server-side.
Local issuer/audience checks additionally pin it to the configured project.
Never configure an endpoint from request data.
"""
import base64
import json
import time
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID

def authenticate_supabase_token(token: str, *, project_url: str, anon_key: str) -> str:
    parsed = urlparse(project_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        raise ValueError("invalid configured Supabase project URL")
    if not anon_key or not isinstance(token, str) or token.count(".") != 2 or len(token) > 8192:
        raise PermissionError("invalid token")
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
        if not isinstance(claims, dict):
            raise ValueError("invalid claims")
        expected_issuer = project_url.rstrip("/") + "/auth/v1"
        if claims.get("iss") != expected_issuer or claims.get("aud") != "authenticated":
            raise PermissionError("wrong JWT issuer or audience")
        expiry = claims.get("exp")
        if type(expiry) is not int or expiry <= int(time.time()):
            raise PermissionError("expired JWT")
        subject = str(UUID(claims["sub"]))
    except (KeyError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise PermissionError("invalid JWT claims") from exc

    # The untrusted decoded claims above do NOT authenticate the caller.
    # The project Auth server must verify signature, expiry, and revocation.
    request = Request(
        project_url.rstrip("/") + "/auth/v1/user",
        headers={"Authorization": "Bearer " + token, "apikey": anon_key},
    )
    try:
        with urlopen(request, timeout=8) as response:
            if response.status != 200:
                raise PermissionError("Supabase Auth rejected token")
            user = json.load(response)
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise PermissionError("Supabase Auth verification failed") from exc
    if not isinstance(user, dict) or user.get("id") != subject or user.get("aud") not in (None, "authenticated"):
        raise PermissionError("JWT subject does not match verified user")
    return subject

"""Isolated trusted-server PostgREST adapters; never imported by client code.

Requires a dedicated isolated service-role key. Any transport uncertainty during
publish raises PostCommitUnknown; the caller must reconcile, never delete.
"""
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import UUID
from .finalize_core import PostCommitUnknown

def _rpc(base_url: str, service_key: str, name: str, payload: dict):
    if not base_url.startswith("http://127.0.0.1:56321"):
        raise ValueError("isolated Supabase URL required")
    if not service_key:
        raise PermissionError("isolated service credential missing")
    request = Request(
        base_url.rstrip("/") + "/rest/v1/rpc/" + name,
        data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + service_key,
                 "apikey": service_key, "Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=10) as response:
        if response.status not in (200, 201):
            raise RuntimeError("unexpected RPC response")
        return json.load(response)

def publish_post(base_url: str, service_key: str, owner: str, path: str, content: str) -> str:
    try:
        result = _rpc(base_url, service_key, "video_qa_publish",
                      {"p_owner": str(UUID(owner)), "p_path": path, "p_content": content})
    except HTTPError as exc:
        # A PostgREST error can be definite rejection, but a gateway can also
        # fail after commit. Preserve staged bytes in every ambiguous case.
        raise PostCommitUnknown("publish response not authoritative") from exc
    except (URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
        raise PostCommitUnknown("publish outcome unknown") from exc
    return str(UUID(result))

def reconcile_post(base_url: str, service_key: str, owner: str, path: str) -> str | None:
    result = _rpc(base_url, service_key, "video_qa_reconcile",
                  {"p_owner": str(UUID(owner)), "p_path": path})
    return None if result is None else str(UUID(result))

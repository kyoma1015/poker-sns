"""Isolated integration composition. Not a deployed endpoint.

Deliberately fails closed for delete/cleanup until immutable Storage object
versioning and a durable cleanup worker are implemented. This composition is
for read-only authenticated flows and isolated contract QA only.
"""
from .finalize_boundary import ServerAdapters
from .supabase_auth_adapter import authenticate_supabase_token
from .storage_download_adapter import download_private_staged
from .isolated_db_adapter import publish_post, reconcile_post

def build_isolated_adapters(*, project_url: str, anon_key: str, service_key: str, access_token: str):
    # The per-request access token must be the same token verified by Auth.
    # Never instantiate a shared adapter for multiple callers.
    def authenticate(token: str) -> str:
        if token != access_token:
            raise PermissionError("request token differs from scoped token")
        return authenticate_supabase_token(token, project_url=project_url, anon_key=anon_key)
    def owner(user: str, path: str) -> bool:
        # This is a necessary path constraint, NOT proof of immutable ownership.
        # The Storage read itself must pass RLS with this user's verified JWT.
        return path.startswith(user + "/") and path.count("/") == 1
    def staged(user: str, path: str):
        return download_private_staged(user, path, project_url=project_url,
                                       anon_key=anon_key, access_token=access_token)
    def publish(user: str, path: str, content: str):
        return publish_post(project_url, service_key, user, path, content)
    def reconcile(user: str, path: str):
        return reconcile_post(project_url, service_key, user, path)
    def unsupported_delete(path: str):
        raise RuntimeError("immutable Storage delete not implemented: fail closed")
    def unsupported_cleanup(user: str, path: str):
        raise RuntimeError("durable cleanup enqueue not implemented: fail closed")
    return ServerAdapters(authenticate, owner, staged, publish,
                          unsupported_delete, reconcile, unsupported_cleanup)

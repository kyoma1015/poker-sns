"""Fail-closed isolated Storage deletion capability.

Supabase Storage remove(path) is not a compare-and-delete operation: a HEAD
or metadata version check followed by remove is subject to a replacement
race (ABA). No unversioned delete is permitted here.
"""

class ConditionalDeleteUnavailable(RuntimeError):
    pass

def delete_if_exact_version(owner: str, path: str, expected_version: str) -> bool:
    """Do not remove an object until atomic version-conditioned API is proven."""
    if not owner or not path.startswith(owner + "/") or not expected_version:
        raise PermissionError("invalid object identity or version")
    raise ConditionalDeleteUnavailable(
        "Storage REST remove has no verified atomic If-Match/version precondition"
    )

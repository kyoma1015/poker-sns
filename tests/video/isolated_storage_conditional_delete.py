"""Fail-closed isolated Storage deletion capability.

Supabase Storage remove(path) is not a compare-and-delete operation: a HEAD
or metadata version check followed by remove is subject to a replacement
race (ABA). No unversioned delete is permitted here.
"""

class ConditionalDeleteUnavailable(RuntimeError):
    pass

def delete_if_exact_version(owner: str, path: str, expected_version: str) -> bool:
    """Do not remove an object until atomic version-conditioned API is proven."""
    from uuid import UUID
    try:
        canonical_owner = str(UUID(owner))
        if owner != canonical_owner:
            raise ValueError("noncanonical owner")
        segments = path.split("/")
        if len(segments) != 2 or segments[0] != canonical_owner:
            raise ValueError("owner path mismatch")
        stem, dot, ext = segments[1].rpartition(".")
        if not dot or ext not in ("mp4", "webm"):
            raise ValueError("invalid extension")
        if str(UUID(stem)) != stem:
            raise ValueError("noncanonical object UUID")
        if not isinstance(expected_version, str) or not expected_version.strip():
            raise ValueError("missing version")
    except (ValueError, TypeError, AttributeError):
        raise PermissionError("invalid object identity or version") from None
    raise ConditionalDeleteUnavailable(
        "Storage REST remove has no verified atomic If-Match/version precondition"
    )

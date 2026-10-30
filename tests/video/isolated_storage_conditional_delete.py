"""Fail-closed isolated Storage deletion capability.

Supabase storage-js StorageFileApi.remove(paths) sends only {prefixes: paths}\nto /object/{bucket}; there is no expected generation in the request. A HEAD\nor metadata version check followed by remove is subject to a replacement\nrace (ABA). No unversioned delete is permitted here.\nSource: https://github.com/supabase/storage-js/blob/main/src/packages/StorageFileApi.ts
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
    # Deliberately never issue Storage REST DELETE, including after a
    # successful generation inspection: the current StorageFileApi.remove
    # sends only {prefixes: paths}, so an ABA replacement would be removed.
    raise ConditionalDeleteUnavailable(
        "Storage REST remove has no verified atomic If-Match/version precondition"
    )

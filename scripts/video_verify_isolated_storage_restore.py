#!/usr/bin/env python3
"""Offline byte-level Storage restore rehearsal. NEVER calls a Supabase API."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def restore(bundle, destination):
    bundle = Path(bundle).resolve(strict=True)
    storage = bundle / "storage"
    manifest = json.loads((storage / "storage-manifest.json").read_text())
    objects = manifest["objects"]
    if not isinstance(objects, list) or not isinstance(manifest.get("buckets"), int):
        raise ValueError("Invalid Storage manifest")
    destination = Path(destination)
    # Reject pre-existing destinations. Never overwrite potentially important data.
    if destination.exists() or destination.is_symlink():
        raise ValueError("Restore destination already exists")
    destination.mkdir(mode=0o700, parents=False)
    seen = set()
    try:
        for row in objects:
            name = row["path"]
            path = Path(name)
            if (not isinstance(name, str) or not name or path.is_absolute()
                    or len(path.parts) < 2 or any(part in ("", ".", "..") for part in path.parts)
                    or name in seen or "\\" in name):
                raise ValueError("Unsafe or duplicate object path")
            if path.parts[0] not in bucket_ids:
                raise ValueError("Unknown restored Storage bucket")
            seen.add(name)
            source = storage / path
            if not source.is_file() or source.is_symlink():
                raise ValueError("Missing or linked source object")
            if source.stat().st_size != row["bytes"] or digest(source) != row["sha256"]:
                raise ValueError("Source object integrity mismatch")
            target = destination / path
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open("rb") as src, target.open("xb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            if target.stat().st_size != row["bytes"] or digest(target) != row["sha256"]:
                raise ValueError("Restored object integrity mismatch")
        actual = {str(p.relative_to(storage)) for p in storage.rglob("*") if p.is_file()}
        if actual != seen | {"storage-manifest.json"}:
            raise ValueError("Unexpected source objects")
        restored = {str(p.relative_to(destination)) for p in destination.rglob("*") if p.is_file()}
        if restored != seen or len({p.split("/", 1)[0] for p in seen}) != manifest["buckets"]:
            raise ValueError("Restore inventory mismatch")
    except Exception:
        shutil.rmtree(destination)
        raise
    print("PASS: isolated filesystem Storage bytes restored and matched SHA256")
    print("NOT VERIFIED: Supabase Storage API, bucket policy, DB metadata or auth/RLS")

if __name__ == "__main__":
    try:
        if len(sys.argv) != 3:
            raise ValueError("Usage: video_verify_isolated_storage_restore.py BUNDLE_DIR NEW_EMPTY_DESTINATION")
        restore(sys.argv[1], sys.argv[2])
    except Exception as error:
        print("FAIL: offline Storage restore rehearsal:", type(error).__name__, file=sys.stderr)
        sys.exit(2)

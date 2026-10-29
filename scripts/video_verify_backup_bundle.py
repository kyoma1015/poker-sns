#!/usr/bin/env python3
"""Offline verification of decrypted DB and Storage bytes. Not a DB/Storage restore."""
import hashlib
import json
from pathlib import Path
import sys

def checksum(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main(root):
    root=Path(root).resolve(strict=True)
    lines=(root/"database.sha256").read_text().splitlines()
    if len(lines)!=1 or not lines[0].endswith("  database.dump"):
        raise RuntimeError("Invalid DB checksum file")
    digest=lines[0].split("  ",1)[0]
    if checksum(root/"database.dump")!=digest:
        raise RuntimeError("Database checksum mismatch")
    storage=root/"storage"
    manifest=json.loads((storage/"storage-manifest.json").read_text())
    rows=manifest["objects"]
    seen=set()
    for row in rows:
        name=row["path"]
        p=Path(name)
        if p.is_absolute() or ".." in p.parts or name in seen:
            raise RuntimeError("Unsafe or duplicate Storage path")
        seen.add(name)
        file=storage/p
        if not file.is_file() or file.is_symlink():
            raise RuntimeError("Missing Storage file")
        if file.stat().st_size!=row["bytes"] or checksum(file)!=row["sha256"]:
            raise RuntimeError("Storage checksum mismatch")
    actual={str(p.relative_to(storage)) for p in storage.rglob("*") if p.is_file()}
    if actual != seen | {"storage-manifest.json"}:
        raise RuntimeError("Unexpected or missing Storage file")
    print("PASS: encrypted archive contents, DB SHA256, Storage byte SHA256 verified.")
    print("NOT VERIFIED: full PostgreSQL restore, Supabase auth/RLS and Storage API restore.")

if __name__=="__main__":
    try:
        if len(sys.argv)!=2: raise RuntimeError("Usage: video_verify_backup_bundle.py <decrypted-bundle-dir>")
        main(sys.argv[1])
    except Exception as e:
        print("FAIL: backup integrity verification:",type(e).__name__,file=sys.stderr)
        sys.exit(2)

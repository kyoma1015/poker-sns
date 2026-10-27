#!/usr/bin/env python3
"""Private, read-only Supabase Storage byte export. Never run in CI or commit output."""
import getpass
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

PROJECT = "ephptepeuespnxtzdqby"
BASE = f"https://{PROJECT}.supabase.co"
PAGE = 100
MAX_FILE = 100 * 1024 * 1024

def fail(message):
    raise SystemExit(f"ERROR: {message}")

def request(method, path, key, payload=None):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers={
        "apikey": key, "Authorization": "Bearer " + key,
        "Content-Type": "application/json", "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=45) as response:
        if response.geturl().split("/")[2] != urllib.parse.urlparse(BASE).netloc:
            fail("cross-origin redirect refused")
        return response.read()

def list_objects(bucket, prefix, key):
    offset = 0
    while True:
        path = "/storage/v1/object/list/" + urllib.parse.quote(bucket, safe="")
        items = json.loads(request("POST", path, key, {
            "prefix": prefix, "limit": PAGE, "offset": offset,
            "sortBy": {"column": "name", "order": "asc"}
        }))
        if not isinstance(items, list):
            fail("unexpected listing response")
        for item in items:
            name = item.get("name")
            if not isinstance(name, str) or name in (".", "..") or "/" in name or chr(92) in name:
                fail("unsafe object name")
            full = prefix + name
            if item.get("id") is None:
                yield from list_objects(bucket, full + "/", key)
            else:
                yield full
        if len(items) < PAGE:
            break
        offset += PAGE

def main():
    if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
        fail("production export prohibited in CI")
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        fail("trusted interactive terminal required")
    root = Path.home() / "PokerID-Private-Backups"
    if root.is_symlink():
        fail("backup root is symlink")
    root.mkdir(mode=0o700, exist_ok=True)
    if root.stat().st_mode & 0o777 != 0o700:
        fail("backup root must have mode 0700")
    dest = root / ("storage-export-" + __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    dest.mkdir(mode=0o700)
    key = getpass.getpass("Supabase service-role key (hidden, never saved): ").strip()
    if not key:
        fail("missing key")
    try:
        buckets = json.loads(request("GET", "/storage/v1/bucket", key))
        if not isinstance(buckets, list):
            fail("unexpected buckets response")
        manifest = []
        for bucket in buckets:
            bucket_id = bucket.get("id")
            if not isinstance(bucket_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", bucket_id):
                fail("invalid bucket identifier")
            for name in list_objects(bucket_id, "", key):
                parts = name.split("/")
                if any(p in ("", ".", "..") for p in parts):
                    fail("unsafe object path")
                target = dest / "objects" / bucket_id
                for part in parts[:-1]:
                    target = target / part
                    if target.is_symlink():
                        fail("symlink in output path")
                    target.mkdir(mode=0o700, parents=True, exist_ok=True)
                target.mkdir(mode=0o700, parents=True, exist_ok=True)
                output = target / parts[-1]
                if output.exists() or output.is_symlink():
                    fail("duplicate object path")
                object_path = "/storage/v1/object/authenticated/" + urllib.parse.quote(bucket_id, safe="") + "/" + urllib.parse.quote(name, safe="/")
                data = request("GET", object_path, key)
                if len(data) > MAX_FILE:
                    fail("object exceeds 100 MiB export cap")
                with output.open("xb") as f:
                    os.chmod(output, 0o600)
                    f.write(data)
                manifest.append({"bucket": bucket_id, "name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        manifest_path = dest / "storage-manifest.json"
        with manifest_path.open("x", encoding="utf-8") as f:
            os.chmod(manifest_path, 0o600)
            json.dump({"project": PROJECT, "objects": manifest, "bucket_count": len(buckets)}, f, indent=2, ensure_ascii=False)
        print(f"Storage byte export completed locally: {len(manifest)} objects, {len(buckets)} buckets.")
        print(f"Private path: {dest}")
        print("NOT a verified recovery point: independently restore all objects and compare checksums.")
    except (urllib.error.URLError, ValueError, OSError) as e:
        fail(f"export incomplete; preserve private partial output for secure cleanup ({type(e).__name__})")

if __name__ == "__main__":
    main()

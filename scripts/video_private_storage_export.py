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

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("redirect refused before forwarding credentials")

OPENER = urllib.request.build_opener(NoRedirect())

def request(method, path, key, payload=None, max_bytes=8 * 1024 * 1024):
    body = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=body, method=method, headers={
        "apikey": key, "Authorization": "Bearer " + key,
        "Content-Type": "application/json", "Accept": "application/json",
    })
    with OPENER.open(req, timeout=45) as response:
        if response.geturl().split("/")[2] != urllib.parse.urlparse(BASE).netloc:
            fail("cross-origin redirect refused")
        data = response.read(max_bytes + 1)
        if len(data) > max_bytes:
            fail("response exceeds export cap")
        return data

def list_objects(bucket, prefix, key):
    if prefix.count("/") > 64:
        fail("object nesting exceeds safe export limit")
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
            if not isinstance(name, str) or not name or name in (".", "..") or "/" in name or chr(92) in name:
                fail("unsafe object name")
            full = prefix + name
            if item.get("id") is None:
                yield from list_objects(bucket, full + "/", key)
            else:
                yield {"name": full, "id": item["id"], "updated_at": item.get("updated_at"), "metadata": item.get("metadata")}
        if len(items) < PAGE:
            break
        offset += PAGE

def inventory(buckets, key):
    result = {}
    for bucket in buckets:
        bucket_id = bucket.get("id")
        if not isinstance(bucket_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", bucket_id):
            fail("invalid bucket identifier")
        if bucket_id in result:
            fail("duplicate bucket")
        items = list(list_objects(bucket_id, "", key))
        if len({item["name"] for item in items}) != len(items):
            fail("duplicate inventory object")
        result[bucket_id] = items
    return result

def write_private(path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(data)
        output.flush()
        os.fsync(output.fileno())

def verify_export(dest):
    dest = Path(dest)
    manifest = json.loads((dest / "storage-manifest.json").read_text())
    expected = set()
    for item in manifest["objects"]:
        parts = [item["bucket"], *item["name"].split("/")]
        if any(p in ("", ".", "..") or "\\" in p for p in parts):
            fail("unsafe manifest path")
        path = dest / "objects"
        for part in parts:
            path /= part
            if path.is_symlink():
                fail("symlink in export")
        if path in expected:
            fail("duplicate manifest object")
        expected.add(path)
        data = path.read_bytes()
        if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
            fail("export checksum mismatch")
    actual = {p for p in (dest / "objects").rglob("*") if p.is_file()}
    if actual != expected:
        fail("export inventory mismatch")
    return len(expected)

def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--verify":
        print(f"Verified {verify_export(sys.argv[2])} exported objects; remote restore remains required.")
        return
    os.umask(0o077)
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
        before = inventory(buckets, key)
        manifest = []
        for bucket in buckets:
            bucket_id = bucket.get("id")
            if not isinstance(bucket_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", bucket_id):
                fail("invalid bucket identifier")
            for entry in before[bucket_id]:
                name = entry["name"]
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
                data = request("GET", object_path, key, max_bytes=MAX_FILE)
                if len(data) > MAX_FILE:
                    fail("object exceeds 100 MiB export cap")
                write_private(output, data)
                manifest.append({"bucket": bucket_id, "name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
        after_buckets = json.loads(request("GET", "/storage/v1/bucket", key))
        if after_buckets != buckets or inventory(after_buckets, key) != before:
            fail("Storage changed during export; no completed manifest written")
        write_private(dest / "storage-buckets.json", json.dumps(buckets, ensure_ascii=False).encode())
        write_private(dest / "storage-inventory.json", json.dumps(before, ensure_ascii=False).encode())
        write_private(dest / "storage-manifest.json", json.dumps({"project": PROJECT, "objects": manifest, "bucket_count": len(buckets)}, indent=2, ensure_ascii=False).encode())
        verify_export(dest)
        print(f"Storage byte export completed locally: {len(manifest)} objects, {len(buckets)} buckets.")
        print(f"Private path: {dest}")
        print("NOT a verified recovery point: independently restore all objects and compare checksums.")
    except (urllib.error.URLError, ValueError, OSError) as e:
        fail(f"export incomplete; preserve private partial output for secure cleanup ({type(e).__name__})")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Read-only Supabase Storage byte exporter. Never logs credentials or object data."""
import hashlib
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

def required(name):
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"Missing required setting: {name}")
    return value

def inventory_snapshot(rows):
    """Canonicalize listing identity/revision for safe two-pass comparison."""
    return sorted((bucket, key, json.dumps(revision, sort_keys=True, separators=(",", ":")))
                  for bucket, key, revision in rows)


def inventory_unchanged(before, after):
    return inventory_snapshot(before) == inventory_snapshot(after)


def bucket_snapshot(buckets):
    """Compare every exposed bucket setting, not just bucket names."""
    return sorted(json.dumps(b, sort_keys=True, separators=(",", ":")) for b in buckets)


def buckets_unchanged(before, after):
    return bucket_snapshot(before) == bucket_snapshot(after)


def auth_headers(token):
    """Modern sb_secret keys belong only in apikey; legacy JWT keys may be Bearer."""
    if token.startswith("sb_secret_"):
        return {"apikey": token}
    if token.count(".") == 2 and not token.startswith("sb_"):
        return {"apikey": token, "Authorization": "Bearer " + token}
    raise RuntimeError("Unsupported Storage credential type")


def main():
    base = required("PROD_SUPABASE_URL").rstrip("/")
    if base != "https://ephptepeuespnxtzdqby.supabase.co":
        raise RuntimeError("Incorrect production project API origin")
    token = required("PROD_STORAGE_READ_KEY")
    storage_headers = auth_headers(token)
    output = Path(required("BACKUP_STORAGE_DIR")).resolve()
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    class NoExternalRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(base).netloc:
                raise RuntimeError("Storage redirect left trusted project origin")
            return super().redirect_request(req, fp, code, msg, headers, newurl)
    opener = urllib.request.build_opener(NoExternalRedirect())
    def request(path, data=None):
        headers = storage_headers.copy()
        if data is not None: headers["Content-Type"] = "application/json"
        req = urllib.request.Request(base + "/storage/v1/" + path, data=data, headers=headers)
        return opener.open(req, timeout=40)
    with request("bucket") as response:
        buckets = json.load(response)
    if not isinstance(buckets, list):
        raise RuntimeError("Storage bucket inventory failed")
    manifest = []
    first_inventory = []
    def enumerate_prefix(bucket, prefix, depth=0):
        if depth > 32:
            raise RuntimeError("Unexpected folder depth")
        offset = 0
        while True:
            payload = json.dumps({"prefix":prefix, "limit":100, "offset":offset,
                                  "sortBy":{"column":"name","order":"asc"}}).encode()
            with request("object/list/" + urllib.parse.quote(bucket,safe=""), payload) as response:
                rows = json.load(response)
            if not isinstance(rows, list):
                raise RuntimeError("Invalid object listing")
            for item in rows:
                name = item.get("name")
                if not isinstance(name,str) or not name or "/" in name or name in (".",".."):
                    raise RuntimeError("Invalid object name")
                full = prefix + name
                if item.get("id") is None:
                    yield from enumerate_prefix(bucket, full + "/", depth+1)
                else:
                    # Capture object identity and available revision metadata on each listing.
                    # A stable path alone does not detect in-place overwrites.
                    revision = {k: item.get(k) for k in ("id", "updated_at", "metadata")}
                    yield full, revision
            if len(rows) < 100: break
            offset += len(rows)
    for bucket_record in buckets:
        bucket = bucket_record["id"]
        if not isinstance(bucket,str) or bucket in ("", ".", "..") or "/" in bucket:
            raise RuntimeError("Invalid bucket ID")
        for key, revision in enumerate_prefix(bucket, ""):
            first_inventory.append((bucket, key, revision))
            parts = key.split("/")
            if any(p in ("", ".", "..") for p in parts):
                raise RuntimeError("Invalid object path")
            target = output / bucket / Path(*parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_symlink() or target.exists():
                raise RuntimeError("Duplicate or unsafe destination")
            relative = str(target.relative_to(output))
            encoded_key = "/".join(urllib.parse.quote(p,safe="") for p in parts)
            urlpath = "object/authenticated/" + urllib.parse.quote(bucket,safe="") + "/" + encoded_key
            digest = hashlib.sha256()
            size = 0
            with request(urlpath) as response, target.open("xb") as stream:
                os.chmod(target,0o600)
                while True:
                    chunk = response.read(1024*1024)
                    if not chunk: break
                    stream.write(chunk)
                    digest.update(chunk)
                    size += len(chunk)
            manifest.append({"path":relative,"bytes":size,"sha256":digest.hexdigest()})
    expected = int(required("EXPECTED_STORAGE_OBJECTS"))
    if len(manifest) != expected or len(buckets) != int(required("EXPECTED_STORAGE_BUCKETS")):
        raise RuntimeError("Inventory changed. Refusing to certify incomplete snapshot.")
    # Re-list and require the object paths to remain unchanged during export.
    second_inventory = [(b["id"], k, revision)
                        for b in buckets for k, revision in enumerate_prefix(b["id"],"")]
    if not inventory_unchanged(first_inventory, second_inventory):
        raise RuntimeError("Storage object identity or revision changed during download")
    with request("bucket") as response:
        final_buckets = json.load(response)
    if not isinstance(final_buckets, list) or not buckets_unchanged(buckets, final_buckets):
        raise RuntimeError("Storage bucket configuration changed during download")
    manifest_path = output / "storage-manifest.json"
    manifest_path.write_text(json.dumps({"objects":manifest,"buckets":len(buckets),
                                          "bucket_records":buckets},indent=2))
    os.chmod(manifest_path,0o600)
    print("Storage bytes downloaded and SHA256 recorded:", len(manifest),
          "objects; restore validation still required")

if __name__ == "__main__":
    try: main()
    except Exception as error:
        print("Storage export failed:", type(error).__name__, str(error) if "Missing required" in str(error) else "see privileged operator logs",file=sys.stderr)
        raise SystemExit(2)

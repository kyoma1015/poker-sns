import importlib.util
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('exporter', 'scripts/video_private_storage_export.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def write_manifest(root, objects):
    buckets = [{"id": "bucket"}]
    inventory = {"bucket": [{"name": item["name"]} for item in objects]}
    metadata = {"storage-buckets.json": json.dumps(buckets).encode(), "storage-inventory.json": json.dumps(inventory).encode()}
    for name, data in metadata.items(): (root / name).write_bytes(data)
    manifest = {"version":2, "project":m.PROJECT, "bucket_count":1, "objects":objects,
                "metadata_sha256":{name:hashlib.sha256(data).hexdigest() for name,data in metadata.items()}}
    (root / "storage-manifest.json").write_text(json.dumps(manifest))

class ExportTests(unittest.TestCase):
    def test_redirect_blocked_before_credentials_forwarded(self):
        with self.assertRaises(ValueError):
            m.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://evil.invalid')

    def test_bounded_response(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def geturl(self): return m.BASE
            def read(self, count):
                self.count = count
                return b'12345'
        response = Response()
        with patch.object(m.OPENER, 'open', return_value=response):
            with self.assertRaises(SystemExit): m.request('GET', '/test', 'fake', max_bytes=4)
        self.assertEqual(response.count, 5)

    def test_checksum_and_inventory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / 'objects' / 'bucket' / 'a'
            file.parent.mkdir(parents=True)
            m.write_private(file, b'abc')
            self.assertEqual(file.stat().st_mode & 0o777, 0o600)
            manifest = {'objects': [{'bucket':'bucket','name':'a','bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest()}]}
            write_manifest(root, manifest["objects"])
            self.assertEqual(m.verify_export(root), 1)
            file.write_bytes(b'bad')
            with self.assertRaises(SystemExit): m.verify_export(root)
            file.write_bytes(b'abc')
            (file.parent / 'extra').write_bytes(b'x')
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'objects').mkdir()
            (root / 'objects' / 'bucket').symlink_to(root, target_is_directory=True)
            write_manifest(root, [{'bucket':'bucket','name':'a','bytes':0,'sha256':''}])
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_metadata_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(root, [])
            self.assertEqual(m.verify_export(root), 0)
            (root / "storage-buckets.json").write_text('[]')
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_missing_inventory_object_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_manifest(root, [])
            data = json.dumps({"bucket":[{"name":"missing"}]}).encode()
            (root / "storage-inventory.json").write_bytes(data)
            path = root / "storage-manifest.json"
            manifest = json.loads(path.read_text())
            manifest["metadata_sha256"]["storage-inventory.json"] = hashlib.sha256(data).hexdigest()
            path.write_text(json.dumps(manifest))
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_legacy_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "storage-manifest.json").write_text('{"objects":[]}')
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_duplicate_inventory_rejected(self):
        with patch.object(m, 'list_objects', return_value=iter([{'name':'a'}, {'name':'a'}])):
            with self.assertRaises(SystemExit): m.inventory([{'id':'bucket'}], 'fake')

if __name__ == '__main__': unittest.main()

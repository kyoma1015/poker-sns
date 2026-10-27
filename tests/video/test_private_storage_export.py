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
            (root / 'storage-manifest.json').write_text(json.dumps(manifest))
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
            (root / 'storage-manifest.json').write_text(json.dumps({'objects':[{'bucket':'bucket','name':'a','bytes':0,'sha256':''}]}))
            with self.assertRaises(SystemExit): m.verify_export(root)

    def test_duplicate_inventory_rejected(self):
        with patch.object(m, 'list_objects', return_value=iter([{'name':'a'}, {'name':'a'}])):
            with self.assertRaises(SystemExit): m.inventory([{'id':'bucket'}], 'fake')

if __name__ == '__main__': unittest.main()

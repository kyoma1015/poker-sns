"""Synthetic-only tests for offline video backup checks. Never contact production."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "video_verify_backup_bundle.py"
STORAGE_SCRIPT = SCRIPT.with_name("video_backup_storage.py")
spec = importlib.util.spec_from_file_location("video_backup_storage", STORAGE_SCRIPT)
storage_backup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage_backup)

class BackupIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root/"database.dump").write_bytes(b"synthetic-db")
        (self.root/"database.sha256").write_text(hashlib.sha256(b"synthetic-db").hexdigest()+"  database.dump\n")
        (self.root/"storage"/"bucket").mkdir(parents=True)
        self.file = self.root/"storage"/"bucket"/"video.mp4"
        self.file.write_bytes(b"synthetic-video")
        self.manifest = self.root/"storage"/"storage-manifest.json"
        self.write_manifest("bucket/video.mp4")

    def write_manifest(self, path):
        self.manifest.write_text(json.dumps({"buckets":1,"objects":[{"path":path, "bytes":len(b"synthetic-video"), "sha256":hashlib.sha256(b"synthetic-video").hexdigest()}]}))

    def run_check(self):
        return subprocess.run([sys.executable,str(SCRIPT),str(self.root)],capture_output=True,text=True,timeout=8)

    def test_valid_bundle_passes(self):
        self.assertEqual(self.run_check().returncode, 0)

    def test_modified_storage_bytes_fail(self):
        self.file.write_bytes(b"tampered-video")
        self.assertNotEqual(self.run_check().returncode,0)

    def test_modified_db_bytes_fail(self):
        (self.root/"database.dump").write_bytes(b"tampered-db")
        self.assertNotEqual(self.run_check().returncode,0)

    def test_manifest_path_traversal_fails(self):
        self.write_manifest("../outside")
        self.assertNotEqual(self.run_check().returncode,0)

    def test_missing_file_fails(self):
        self.file.unlink()
        self.assertNotEqual(self.run_check().returncode,0)

    def test_extra_file_fails(self):
        (self.root/"storage"/"bucket"/"other").write_bytes(b"extra")
        self.assertNotEqual(self.run_check().returncode,0)

class StorageRevisionTests(unittest.TestCase):
    def setUp(self):
        self.original = [("photos", "same/path.jpg", {"id": "obj-1", "updated_at": "t1", "metadata": {"size": 12}})]

    def test_identical_listing_passes(self):
        self.assertTrue(storage_backup.inventory_unchanged(self.original, list(self.original)))

    def test_same_name_changed_revision_fails(self):
        changed = [("photos", "same/path.jpg", {"id": "obj-1", "updated_at": "t2", "metadata": {"size": 12}})]
        self.assertFalse(storage_backup.inventory_unchanged(self.original, changed))

    def test_same_name_changed_object_id_fails(self):
        changed = [("photos", "same/path.jpg", {"id": "obj-2", "updated_at": "t1", "metadata": {"size": 12}})]
        self.assertFalse(storage_backup.inventory_unchanged(self.original, changed))

    def test_same_name_changed_metadata_fails(self):
        changed = [("photos", "same/path.jpg", {"id": "obj-1", "updated_at": "t1", "metadata": {"size": 13}})]
        self.assertFalse(storage_backup.inventory_unchanged(self.original, changed))

    def test_list_order_does_not_matter(self):
        other = ("photos", "other.jpg", {"id": "obj-3", "updated_at": "t1"})
        self.assertTrue(storage_backup.inventory_unchanged(self.original + [other], [other] + self.original))

    def test_added_or_deleted_path_fails(self):
        self.assertFalse(storage_backup.inventory_unchanged(self.original, []))


if __name__ == "__main__":
    unittest.main()

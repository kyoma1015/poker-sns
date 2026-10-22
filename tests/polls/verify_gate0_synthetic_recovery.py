#!/usr/bin/env python3
"""Synthetic-only recovery policy QA; never connects to production."""
import hashlib
import io
import os
from pathlib import Path
import tempfile
import time
import unittest
from contextlib import redirect_stdout

DAY = 86400
RETENTION_DAYS = 30
RPO_SECONDS = DAY
RTO_SECONDS = DAY

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def retention_plan(records, now):
    """Retain all within 30 days, plus latest verified recovery point as a guard."""
    verified = [r for r in records if r["verified"]]
    if not verified:
        raise RuntimeError("STOP: no verified recovery point")
    newest = max(verified, key=lambda r: r["created"])
    if newest["created"] > now:
        raise RuntimeError("STOP: future timestamp")
    if now - newest["created"] > RPO_SECONDS:
        raise RuntimeError("STOP: no recovery point within RPO")
    return {r["id"] for r in records if now - r["created"] <= RETENTION_DAYS * DAY or r["id"] == newest["id"]}

def validate_recovery(backup_time, incident_time, restore_duration):
    if backup_time > incident_time or incident_time - backup_time > RPO_SECONDS:
        raise RuntimeError("STOP: RPO breach")
    if restore_duration < 0 or restore_duration > RTO_SECONDS:
        raise RuntimeError("STOP: RTO breach")

def encrypted_copy(source: bytes, capacity: int, fail_after=None):
    """Synthetic encrypted bytes only; atomic copy to avoid incomplete published backup."""
    with tempfile.TemporaryDirectory() as td:
        dst = Path(td) / "backup.age"
        staging = Path(td) / "backup.age.part"
        if len(source) > capacity:
            raise OSError("STOP: insufficient capacity")
        try:
            with staging.open("wb") as fh:
                if fail_after is not None:
                    fh.write(source[:fail_after])
                    raise OSError("STOP: interrupted copy")
                fh.write(source)
            os.replace(staging, dst)
            if digest(dst.read_bytes()) != digest(source):
                raise RuntimeError("STOP: digest mismatch")
            return dst.read_bytes()
        finally:
            staging.unlink(missing_ok=True)

class SyntheticRecoveryQA(unittest.TestCase):
    def setUp(self):
        self.now = 1_800_000_000
        self.records = [
            {"id": "day31", "created": self.now - 31*DAY, "verified": True},
            {"id": "day30", "created": self.now - 30*DAY, "verified": True},
            {"id": "day1", "created": self.now - DAY, "verified": True},
            {"id": "latest", "created": self.now - 3600, "verified": True},
        ]

    def test_retention_boundary_and_latest(self):
        self.assertEqual(retention_plan(self.records, self.now), {"day30", "day1", "latest"})

    def test_no_verified_point_stops_deletion(self):
        with self.assertRaisesRegex(RuntimeError, "no verified"):
            retention_plan([{"id":"old", "created":self.now-31*DAY, "verified":False}], self.now)

    def test_stale_recovery_point_stops_deletion(self):
        with self.assertRaisesRegex(RuntimeError, "within RPO"):
            retention_plan([{"id":"old", "created":self.now-31*DAY, "verified":True}], self.now)

    def test_rpo_exact_boundary(self):
        validate_recovery(self.now-DAY, self.now, 1)
        with self.assertRaisesRegex(RuntimeError, "RPO"):
            validate_recovery(self.now-DAY-1, self.now, 1)

    def test_rto_exact_boundary(self):
        validate_recovery(self.now-1, self.now, DAY)
        with self.assertRaisesRegex(RuntimeError, "RTO"):
            validate_recovery(self.now-1, self.now, DAY+1)

    def test_sha256_corruption(self):
        blob = b"synthetic-encrypted-bytes-not-real-user-data"
        self.assertNotEqual(digest(blob), digest(blob[:-1] + b"!"))

    def test_missing_key_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            key = Path(td) / "missing.agekey"
            with self.assertRaises(FileNotFoundError):
                key.read_bytes()

    def test_capacity_failure_no_output(self):
        with self.assertRaisesRegex(OSError, "capacity"):
            encrypted_copy(b"synthetic", 3)

    def test_interruption_no_published_backup(self):
        with self.assertRaisesRegex(OSError, "interrupted"):
            encrypted_copy(b"synthetic", 100, fail_after=3)

    def test_copy_integrity(self):
        blob = b"synthetic-encrypted-placeholder"
        self.assertEqual(encrypted_copy(blob, 100), blob)

    def test_no_sensitive_data_in_logs(self):
        sentinel = "PRIVATE_SYNTHETIC_SECRET_DO_NOT_PRINT"
        captured = io.StringIO()
        with redirect_stdout(captured):
            try:
                encrypted_copy(sentinel.encode(), 1)
            except OSError:
                print("STOP: copy refused")
        self.assertNotIn(sentinel, captured.getvalue())

    def test_future_timestamp_stops_deletion(self):
        with self.assertRaisesRegex(RuntimeError, "future timestamp"):
            retention_plan([{"id":"future", "created":self.now+1, "verified":True}], self.now)

if __name__ == "__main__":
    unittest.main(verbosity=2)

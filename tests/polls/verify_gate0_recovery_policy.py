#!/usr/bin/env python3
"""Synthetic-only gate 0 recovery-policy checks; no production IO or credentials."""
import hashlib
import io
import json
import logging
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

UTC = timezone.utc
NOW = datetime(2026, 10, 22, 12, tzinfo=UTC)
DAY = timedelta(days=1)
RETENTION = timedelta(days=30)
RPO = DAY
RTO = DAY

def prune(records, now=NOW):
    """Never delete the newest verified recovery point, even when all records are old."""
    verified = [r for r in records if r["verified"]]
    if not verified:
        raise ValueError("no verified recovery point: stop without deletion")
    newest = max(verified, key=lambda r: r["created"])
    keep = [r for r in records if r["created"] >= now - RETENTION or r is newest]
    return keep

def rpo_ok(points, now=NOW):
    if not points or any(p > now for p in points):
        return False
    ordered = sorted(points)
    return all(b - a <= RPO for a, b in zip(ordered, ordered[1:])) and now - ordered[-1] <= RPO

def rto_ok(start, finish):
    return start <= finish and finish - start <= RTO

def digest(data):
    return hashlib.sha256(data).hexdigest()

def restore(ciphertext, expected_hash, key, required_bytes, free_bytes, fail_at=None):
    """Deterministic synthetic restore simulator; never decrypts production data."""
    if key is None:
        raise ValueError("missing key")
    if free_bytes < required_bytes:
        raise OSError("insufficient capacity")
    if digest(ciphertext) != expected_hash:
        raise ValueError("digest mismatch")
    if fail_at == "copy":
        raise IOError("interrupted transfer")
    return bytes(ciphertext)

class Gate0PolicyTests(unittest.TestCase):
    def test_retention_30_day_boundary(self):
        rows = [{"created": NOW - timedelta(days=d), "verified": True} for d in (0, 29, 30, 31)]
        kept = prune(rows)
        self.assertEqual(len(kept), 3)
        self.assertNotIn(rows[-1], kept)

    def test_latest_verified_protected(self):
        rows = [{"created": NOW - timedelta(days=40), "verified": True},
                {"created": NOW - timedelta(days=39), "verified": False}]
        self.assertEqual(prune(rows), rows[:1])

    def test_no_verified_point_fail_closed(self):
        with self.assertRaises(ValueError):
            prune([{"created": NOW, "verified": False}])

    def test_rpo_boundary_and_gaps(self):
        self.assertTrue(rpo_ok([NOW - 2 * DAY, NOW - DAY, NOW]))
        self.assertTrue(rpo_ok([NOW - DAY]))
        self.assertFalse(rpo_ok([NOW - DAY - timedelta(seconds=1)]))
        self.assertFalse(rpo_ok([NOW - 3 * DAY, NOW - DAY]))
        self.assertFalse(rpo_ok([]))
        self.assertFalse(rpo_ok([NOW + timedelta(seconds=1)]))

    def test_rto_boundary_and_overrun(self):
        self.assertTrue(rto_ok(NOW - DAY, NOW))
        self.assertFalse(rto_ok(NOW - DAY - timedelta(seconds=1), NOW))
        self.assertFalse(rto_ok(NOW, NOW - timedelta(seconds=1)))

    def test_digest_and_corruption(self):
        data = b"synthetic poll only: no private data"
        self.assertEqual(restore(data, digest(data), "synthetic-key", len(data), 4096), data)
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            restore(data + b"!", digest(data), "synthetic-key", len(data), 4096)

    def test_missing_key(self):
        with self.assertRaisesRegex(ValueError, "missing key"):
            restore(b"fake", digest(b"fake"), None, 4, 100)

    def test_capacity_boundary(self):
        self.assertEqual(restore(b"fake", digest(b"fake"), "test", 4, 4), b"fake")
        with self.assertRaises(OSError):
            restore(b"fake", digest(b"fake"), "test", 4, 3)

    def test_interrupted_copy(self):
        with self.assertRaises(IOError):
            restore(b"fake", digest(b"fake"), "test", 4, 100, fail_at="copy")

    def test_no_secret_in_logs(self):
        secret = "SYNTHETIC-DO-NOT-PRINT-KEY"
        buf = io.StringIO()
        logger = logging.getLogger("poll-gate0-synthetic")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(buf)
        logger.addHandler(handler)
        try:
            try:
                restore(b"x", digest(b"x"), None, 1, 100)
            except ValueError:
                logger.info("Recovery blocked: missing key")
        finally:
            logger.removeHandler(handler)
            handler.close()
        self.assertNotIn(secret, buf.getvalue())
        self.assertNotIn("SYNTHETIC-DO-NOT-PRINT", buf.getvalue())

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Gate0PolicyTests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {
        "scope": "synthetic-only; NOT production RPO/RTO proof",
        "PASS": result.testsRun - len(result.failures) - len(result.errors),
        "FAIL": len(result.failures) + len(result.errors),
        "BLOCKED": 0,
        "cases": result.testsRun,
    }
    path = os.environ.get("GATE0_REPORT")
    if path:
        Path(path).write_text(json.dumps(report, indent=2) + "\n")
    print(stream.getvalue())
    print("SUMMARY " + json.dumps(report, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)

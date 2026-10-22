#!/usr/bin/env python3
"""Synthetic-only age backup lifecycle; no network, Supabase, credentials or real data."""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

NOW = datetime(2026, 10, 22, tzinfo=timezone.utc)
DAY = timedelta(days=1)
DATA = b"synthetic poll fixture only; no real user data\n"

def sha(data):
    return hashlib.sha256(data).hexdigest()

def age(*args):
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError("age operation failed (details suppressed)")
    return result.stdout

class Lifecycle:
    def __init__(self, root):
        self.root = Path(root)
        for name in ("keys", "source", "offsite", "staging"):
            (self.root / name).mkdir(mode=0o700)
        self.key = self.root / "keys" / "primary.key"
        age("age-keygen", "-o", str(self.key))
        self.key.chmod(0o600)
        self.recipient = age("age-keygen", "-y", str(self.key)).decode().strip()
        self.records = []

    def make(self, label, created, data=DATA, fail=None):
        # Stage ciphertext, copy, verify and decrypt BEFORE publishing a recovery point.
        source = self.root / "source" / (label + ".txt")
        staged = self.root / "staging" / (label + ".age")
        destination = self.root / "offsite" / (label + ".age")
        source.write_bytes(data)
        try:
            if fail == "encrypt":
                raise RuntimeError("injected encryption failure")
            age("age", "-r", self.recipient, "-o", str(staged), str(source))
            if fail == "copy":
                raise RuntimeError("injected interrupted copy")
            copied = self.root / "staging" / (label + ".copy")
            shutil.copyfile(staged, copied)
            if fail == "corrupt":
                copied.write_bytes(copied.read_bytes() + b"damage")
            if sha(staged.read_bytes()) != sha(copied.read_bytes()):
                raise ValueError("SHA256 mismatch")
            restored = self.root / "staging" / (label + ".restored")
            age("age", "-d", "-i", str(self.key), "-o", str(restored), str(copied))
            if restored.read_bytes() != data:
                raise ValueError("plaintext mismatch")
            if fail == "verify":
                raise RuntimeError("injected verification failure")
            os.replace(copied, destination)
            self.records.append({"label": label, "created": created, "digest": sha(destination.read_bytes()), "verified": True})
            return destination
        finally:
            for path in (source, staged, self.root / "staging" / (label + ".copy"), self.root / "staging" / (label + ".restored")):
                path.unlink(missing_ok=True)

    def prune(self):
        verified = [r for r in self.records if r["verified"] and self.valid(r)]
        if not verified:
            raise RuntimeError("no verified backup; deletion blocked")
        newest = max(verified, key=lambda r: r["created"])
        keep = [r for r in self.records if r["created"] >= NOW - 30 * DAY or r is newest]
        for r in self.records:
            if r not in keep:
                (self.root / "offsite" / (r["label"] + ".age")).unlink()
        self.records = keep

    def valid(self, record):
        p = self.root / "offsite" / (record["label"] + ".age")
        return p.is_file() and sha(p.read_bytes()) == record["digest"]

    def latest_valid(self):
        for r in sorted(self.records, key=lambda r: r["created"], reverse=True):
            if self.valid(r):
                return r
        raise RuntimeError("no verified recovery point")

class IntegratedTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.life = Lifecycle(self.tmp.name)

    def test_full_age_roundtrip_and_digest(self):
        p = self.life.make("new", NOW)
        self.assertTrue(self.life.valid(self.life.records[0]))
        self.assertNotIn(DATA, p.read_bytes())
        self.assertEqual(age("age", "-d", "-i", str(self.life.key), str(p)), DATA)

    def test_separate_key_and_offsite(self):
        self.life.make("new", NOW)
        self.assertEqual(self.life.key.stat().st_mode & 0o777, 0o600)
        self.assertEqual(list((self.life.root / "offsite").glob("*.key")), [])

    def test_encryption_failure_preserves_old(self):
        self.life.make("old", NOW - DAY)
        with self.assertRaises(RuntimeError):
            self.life.make("new", NOW, fail="encrypt")
        self.assertEqual(self.life.latest_valid()["label"], "old")

    def test_copy_interruption_preserves_old(self):
        self.life.make("old", NOW - DAY)
        with self.assertRaises(RuntimeError):
            self.life.make("new", NOW, fail="copy")
        self.assertEqual(len(self.life.records), 1)
        self.assertFalse((self.life.root / "offsite" / "new.age").exists())

    def test_corruption_never_published(self):
        self.life.make("old", NOW - DAY)
        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            self.life.make("new", NOW, fail="corrupt")
        self.assertEqual(self.life.latest_valid()["label"], "old")

    def test_verification_failure_preserves_old(self):
        self.life.make("old", NOW - DAY)
        with self.assertRaises(RuntimeError):
            self.life.make("new", NOW, fail="verify")
        self.assertEqual(len(self.life.records), 1)

    def test_latest_corruption_fallback(self):
        self.life.make("old", NOW - DAY)
        p = self.life.make("new", NOW)
        p.write_bytes(p.read_bytes() + b"tampered")
        self.assertEqual(self.life.latest_valid()["label"], "old")

    def test_retention_boundary(self):
        for n, d in (("expired", 31), ("boundary", 30), ("recent", 1)):
            self.life.make(n, NOW - d * DAY)
        self.life.prune()
        self.assertEqual({r["label"] for r in self.life.records}, {"boundary", "recent"})

    def test_only_verified_old_generation_protected(self):
        self.life.make("old", NOW - 40 * DAY)
        self.life.prune()
        self.assertEqual(self.life.latest_valid()["label"], "old")

    def test_no_verified_backup_blocks_prune(self):
        self.life.make("only", NOW - 40 * DAY)
        (self.life.root / "offsite" / "only.age").write_bytes(b"corrupt")
        with self.assertRaisesRegex(RuntimeError, "deletion blocked"):
            self.life.prune()
        self.assertEqual(len(self.life.records), 1)

    def test_wrong_key_rejected(self):
        p = self.life.make("new", NOW)
        other = self.life.root / "keys" / "wrong.key"
        age("age-keygen", "-o", str(other))
        with self.assertRaisesRegex(RuntimeError, "details suppressed"):
            age("age", "-d", "-i", str(other), str(p))

    def test_secret_and_plaintext_not_in_evidence(self):
        p = self.life.make("new", NOW)
        report = json.dumps({"PASS": 1, "FAIL": 0, "BLOCKED": 0, "scope": "synthetic only"})
        self.assertNotIn("AGE-SECRET-KEY-", report)
        self.assertNotIn(DATA.decode().strip(), report)
        self.assertNotIn(b"AGE-SECRET-KEY-", p.read_bytes())
        self.assertNotIn(DATA, p.read_bytes())

if __name__ == "__main__":
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(IntegratedTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    report = {"PASS": result.testsRun - len(result.failures) - len(result.errors),
              "FAIL": len(result.failures) + len(result.errors),
              "BLOCKED": 0, "scope": "synthetic only; NOT a production recovery drill"}
    path = os.environ.get("GATE0_INTEGRATED_REPORT")
    if path:
        Path(path).write_text(json.dumps(report, sort_keys=True) + "\n")
    print(stream.getvalue())
    print("SUMMARY " + json.dumps(report, sort_keys=True))
    raise SystemExit(0 if result.wasSuccessful() else 1)

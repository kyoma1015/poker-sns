import unittest
from tests.video.isolated_orphan_recovery_policy import orphan_recovery_decision

class OrphanPolicyTests(unittest.TestCase):
    def test_posted_is_retained(self):
        self.assertEqual(orphan_recovery_decision(post_exists=True,
            version_pinned=True, atomic_delete_supported=True,
            exclusive_write_lock=True), "retain_posted")
    def test_unversioned_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(post_exists=False,
            version_pinned=False, atomic_delete_supported=True,
            exclusive_write_lock=True), "quarantine_no_version")
    def test_no_atomic_delete_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(post_exists=False,
            version_pinned=True, atomic_delete_supported=False,
            exclusive_write_lock=True), "quarantine_no_atomic_delete")
    def test_no_exclusive_lock_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(post_exists=False,
            version_pinned=True, atomic_delete_supported=True),
            "quarantine_no_exclusive_lock")

if __name__ == "__main__":
    unittest.main()

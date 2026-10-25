import unittest
from tests.video.isolated_orphan_recovery_policy import orphan_recovery_decision

BASE = dict(post_exists=False, version_pinned=True,
            atomic_delete_supported=True, exclusive_write_lock=True,
            key_permanently_reserved=True, all_storage_writers_fenced=True)

class OrphanPolicyTests(unittest.TestCase):
    def test_posted_is_retained(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"post_exists": True})), "retain_posted")

    def test_unversioned_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"version_pinned": False})), "quarantine_no_version")

    def test_unreserved_key_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"key_permanently_reserved": False})), "quarantine_key_reuse_possible")

    def test_unfenced_writer_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"all_storage_writers_fenced": False})), "quarantine_unfenced_storage_writers")

    def test_no_atomic_delete_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"atomic_delete_supported": False})), "quarantine_no_atomic_delete")

    def test_no_exclusive_lock_is_quarantined(self):
        self.assertEqual(orphan_recovery_decision(**(BASE | {"exclusive_write_lock": False})), "quarantine_no_exclusive_lock")

    def test_review_never_authorizes_deletion(self):
        self.assertEqual(orphan_recovery_decision(**BASE), "eligible_for_review_only")

if __name__ == "__main__":
    unittest.main()

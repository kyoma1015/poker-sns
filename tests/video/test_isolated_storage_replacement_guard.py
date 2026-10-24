"""Non-destructive isolated object replacement/ABA threat regression.

No Storage delete is issued. A queue claim, metadata lookup or HTTP ETag
cannot prove atomic conditional removal. Keep orphan bytes quarantined.
"""
import unittest
from tests.video.isolated_orphan_recovery_runbook import plan_orphan_recovery
from tests.video.isolated_storage_conditional_delete import (
    delete_if_exact_version, ConditionalDeleteUnavailable)

class ObjectReplacementSafety(unittest.TestCase):
    def test_replacement_still_blocks_deletion(self):
        owner = "10000000-0000-0000-0000-000000000001"
        path = owner + "/40000000-0000-0000-0000-000000000004.mp4"
        for token in ("etag-a", "etag-b", "etag-a"):
            with self.assertRaises(ConditionalDeleteUnavailable):
                delete_if_exact_version(owner, path, token)

    def test_queue_claim_does_not_grant_delete(self):
        plan = plan_orphan_recovery(
            post_exists=False, pinned_version="etag-a",
            storage_atomic_cas=False, global_write_fence=True)
        self.assertEqual(plan["decision"], "quarantine_no_atomic_delete")
        self.assertFalse(plan["delete_permitted"])

    def test_even_candidate_requires_review(self):
        plan = plan_orphan_recovery(
            post_exists=False, pinned_version="etag-a",
            storage_atomic_cas=True, global_write_fence=True)
        self.assertEqual(plan["decision"], "eligible_for_review_only")
        self.assertFalse(plan["delete_permitted"])

if __name__ == "__main__":
    unittest.main()

"""Review-only production Storage policy boundary.

The isolated SQL fixture intentionally grants owner DELETE for cleanup tests.
Never deploy that policy. Production requires immutable object paths,
non-upsert uploads, no client UPDATE/DELETE, and a reviewed recovery flow.
"""
from pathlib import Path
import unittest

class ProductionPolicyBoundary(unittest.TestCase):
    def test_qa_delete_grant_is_explicitly_blocked(self):
        sql = Path("sql/post_short_videos_candidate.sql").read_text()
        self.assertIn('create policy "post_videos_delete_own"', sql)
        self.assertIn("SECURITY BLOCKER", sql)
        self.assertIn("Production migration MUST NOT grant client DELETE", sql)

if __name__ == "__main__":
    unittest.main()

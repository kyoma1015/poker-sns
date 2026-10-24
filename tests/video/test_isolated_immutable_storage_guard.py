"""Static regression checks for isolated immutable Storage guard."""
from pathlib import Path
import unittest

class ImmutableStorageGuardTests(unittest.TestCase):
    def test_no_owner_mutation_after_guard(self):
        sql = Path("tests/video/isolated_immutable_storage_guard.sql").read_text()
        self.assertIn('drop policy if exists "post_videos_delete_own"', sql)
        self.assertIn('drop policy if exists "post_videos_update_own"', sql)
        self.assertIn("raise exception 'unsafe Storage policy", sql)
    def test_review_policy_has_no_mutation_grant(self):
        sql = Path("sql/post_short_videos_immutable_review_only.sql").read_text().lower()
        self.assertNotIn("for delete to authenticated", sql)
        self.assertNotIn("for update to authenticated", sql)

if __name__ == "__main__":
    unittest.main()

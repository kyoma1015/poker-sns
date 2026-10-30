"""Isolated Storage ABA / revocation security regression checks.

A signed Storage URL is a bearer capability: RLS is checked at issuance,
not at every fetch. Therefore a privacy toggle cannot revoke old URLs.
"""
import unittest
from tests.video.isolated_storage_conditional_delete import (
    ConditionalDeleteUnavailable, delete_if_exact_version)

class VideoStorageSafetyTests(unittest.TestCase):
    def test_aba_does_not_allow_delete(self):
        owner = "10000000-0000-0000-0000-000000000001"
        path = owner + "/30000000-0000-0000-0000-000000000001.mp4"
        # A->B->A cannot be detected by a non-atomic metadata read.
        for observed in ("version-a", "version-b", "version-a"):
            with self.assertRaises(ConditionalDeleteUnavailable):
                delete_if_exact_version(owner, path, observed)

    def test_no_unversioned_delete(self):
        owner = "10000000-0000-0000-0000-000000000001"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner, owner + "/clip.mp4", "")

if __name__ == "__main__":
    unittest.main()

import unittest
from tests.video.isolated_storage_conditional_delete import (
    delete_if_exact_version, ConditionalDeleteUnavailable)

class AtomicDeletionTests(unittest.TestCase):
    def test_version_checked_delete_fails_closed(self):
        owner = "10000000-0000-0000-0000-000000000001"
        with self.assertRaises(ConditionalDeleteUnavailable):
            delete_if_exact_version(owner, owner + "/40000000-0000-0000-0000-000000000004.mp4", "v1")

    def test_missing_version_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner, owner + "/clip.mp4", "")

    def test_other_owner_rejected(self):
        with self.assertRaises(PermissionError):
            delete_if_exact_version("owner-a", "owner-b/clip.mp4", "v1")


    def test_non_uuid_storage_key_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner, owner + "/../private.mp4", "v1")

    def test_non_video_storage_key_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner, owner + "/40000000-0000-0000-0000-000000000004.txt", "v1")

    def test_noncanonical_object_uuid_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        for name in ("40000000000000000000000000000004.mp4",
                     "40000000-0000-0000-0000-000000000004.MP4"):
            with self.subTest(name=name):
                with self.assertRaises(PermissionError):
                    delete_if_exact_version(owner, owner + "/" + name, "v1")

    def test_all_canonical_video_keys_remain_fail_closed(self):
        owner = "10000000-0000-0000-0000-000000000001"
        stem = "40000000-0000-0000-0000-000000000004"
        for extension in ("mp4", "webm"):
            for version in ("v1", "etag:123", "version-with-spaces"):
                with self.subTest(extension=extension, version=version):
                    with self.assertRaises(ConditionalDeleteUnavailable):
                        delete_if_exact_version(
                            owner, owner + "/" + stem + "." + extension, version)

    def test_mismatched_canonical_owner_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        other = "10000000-0000-0000-0000-000000000002"
        stem = "40000000-0000-0000-0000-000000000004"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner, other + "/" + stem + ".mp4", "v1")

    def test_noncanonical_owner_rejected(self):
        owner = "10000000-0000-0000-0000-000000000001"
        stem = "40000000-0000-0000-0000-000000000004"
        with self.assertRaises(PermissionError):
            delete_if_exact_version(owner.upper(),
                                    owner.upper() + "/" + stem + ".mp4", "v1")

if __name__ == "__main__":
    unittest.main()

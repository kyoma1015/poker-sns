import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.video.finalize_core import FinalizeRequest, finalize_video

USER = '10000000-0000-0000-0000-000000000001'
OTHER = '10000000-0000-0000-0000-000000000002'
PATH = USER + '/30000000-0000-0000-0000-000000000001.mp4'

class FinalizeCoreTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.request = FinalizeRequest(USER, PATH, '/tmp/unused.mp4', 'hello')
        self.owner = lambda u, p: u == USER and p == PATH
        self.create = lambda u, p, c: self.calls.append(('post', u, p)) or 'post-id'
        self.cleanup = lambda p: self.calls.append(('delete', p))

    @patch('tests.video.finalize_core.verify', return_value={'duration':2})
    def test_publish_validated(self, verify):
        self.assertEqual(finalize_video(self.request, verify_owner=self.owner,
            create_post=self.create, delete_staged_object=self.cleanup), 'post-id')
        self.assertEqual([x[0] for x in self.calls], ['post'])

    @patch('tests.video.finalize_core.verify', side_effect=ValueError('31s'))
    def test_reject_duration_and_reclaim(self, verify):
        with self.assertRaisesRegex(ValueError,'31s'):
            finalize_video(self.request, verify_owner=self.owner,
                create_post=self.create, delete_staged_object=self.cleanup)
        self.assertEqual(self.calls, [('delete', PATH)])

    @patch('tests.video.finalize_core.verify', return_value={'duration':2})
    def test_failed_db_publish_reclaims(self, verify):
        def fail(*args): raise RuntimeError('DB down')
        with self.assertRaisesRegex(RuntimeError,'DB down'):
            finalize_video(self.request, verify_owner=self.owner,
                create_post=fail, delete_staged_object=self.cleanup)
        self.assertEqual(self.calls, [('delete', PATH)])

    def test_reject_other_user_path_without_side_effect(self):
        with self.assertRaises(ValueError):
            finalize_video(FinalizeRequest(OTHER, PATH, '/tmp/unused.mp4',''),
                verify_owner=self.owner, create_post=self.create,
                delete_staged_object=self.cleanup)
        self.assertEqual(self.calls, [])

    def test_reject_unowned_object_without_side_effect(self):
        with self.assertRaises(PermissionError):
            finalize_video(self.request, verify_owner=lambda u,p:False,
                create_post=self.create, delete_staged_object=self.cleanup)
        self.assertEqual(self.calls, [('delete', PATH)])

    def test_ownership_check_failure_reclaims(self):
        with self.assertRaises(PermissionError):
            finalize_video(self.request, verify_owner=lambda u,p:False,
                create_post=self.create, delete_staged_object=self.cleanup)
        self.assertEqual(self.calls, [('delete', PATH)])

if __name__ == '__main__':
    unittest.main()

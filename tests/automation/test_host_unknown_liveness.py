"""A failed acceptance process must not release a host job with unknown liveness."""
from pathlib import Path
import json
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as worker
from invocation_guard import InvocationGuard
import test_continuation_recovery as fixture


class HostUnknownLiveness(unittest.TestCase):
    def test_acceptance_cleanup_unknown_preserves_running_context(self):
        f=fixture.RecoveryAcceptance();f.setUp()
        try:
            task=f.task()
            q=worker.prepare_host_session(f.repo,f.work,f.state,task,now=100)
            before=json.loads(f.store.db.execute("select evidence from development_jobs where id='next-a'").fetchone()[0])
            error=RuntimeError('owned acceptance cleanup unconfirmed')
            error.worker_liveness_unknown=True
            with patch.object(worker,'validate_and_commit',side_effect=error):
                result=worker.finish_host_session(f.state,'next-a',q['lease_token'],
                    {'task_id':'next-a','dispatch_source':'collaboration','completed':True,
                     'agent_id':'/root/owned_fixture','test_fixture':True},now=101)
            self.assertEqual(result['status'],'blocked')
            status,raw=f.store.db.execute("select status,evidence from development_jobs where id='next-a'").fetchone()
            self.assertEqual(status,'running')
            context=json.loads(raw)
            for key in ('task','before','base_sha','worktree','prepared_for'):
                self.assertEqual(context[key],before[key])
            with self.assertRaises(ValueError):
                with InvocationGuard(f.store,'reject-unknown','/fixture',enabled=True):
                    self.fail('unknown acceptance process taken over')
            self.assertTrue(Path(q['worktree']).is_dir())
        finally:f.tearDown()


if __name__=='__main__':unittest.main()

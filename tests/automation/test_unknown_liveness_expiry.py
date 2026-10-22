"""Unknown liveness survives expiry and observation denial; owned state only."""
from pathlib import Path
import json
import sys
import time
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
import code_worker as worker
import test_continuation_recovery as fixture


class UnknownLivenessExpiry(unittest.TestCase):
    def expiry(self,lane):
        f=fixture.RecoveryAcceptance();f.setUp()
        try:
            def unknown(*args):
                error=RuntimeError('owned unknown cleanup');error.worker_liveness_unknown=True;raise error
            worker.run_task(f.repo,f.work,f.state,f.task(),unknown,timeout=1)
            before=f.store.db.execute("select status,token,evidence from development_jobs where id='next-a'").fetchone()
            self.assertEqual(before[0],'running')
            self.assertIsNone(f.store.leases.claim(f.task('new-task',lane),now=time.time()+10000))
            self.assertEqual(f.store.db.execute("select status,token,evidence from development_jobs where id='next-a'").fetchone(),before)
            self.assertIsNone(f.store.db.execute("select id from development_jobs where id='new-task'").fetchone())
        finally:f.tearDown()

    def test_expired_unknown_blocks_same_lane_without_erasing_context(self):self.expiry('A')
    def test_expired_unknown_blocks_other_lane_without_erasing_context(self):self.expiry('B')

    def test_process_metadata_denial_is_not_process_exit(self):
        with patch.object(Path,'read_text',side_effect=PermissionError('owned denial')):
            with self.assertRaises(worker.WorkerLivenessUnknown):worker._process_stat(999999)

    def test_missing_metadata_remains_known_missing(self):
        with patch.object(Path,'read_text',side_effect=FileNotFoundError()):
            self.assertIsNone(worker._process_stat(999999))

    def test_pending_descendant_observation_denial_retains_unknown(self):
        class Process:
            pid=999998;stdin=None;stdout=None;stderr=None
            def poll(self):return 0
        primary=RuntimeError('owned primary')
        with patch.object(worker,'_descendant_snapshot',return_value={999999:('S',999998,999998,'1')}),patch.object(worker.os,'killpg'),patch.object(Path,'read_text',side_effect=PermissionError('owned denial')):
            # Force a live-leader snapshot but a completed leader at wait checks.
            p=Process();states=iter([None,0,0]);p.poll=lambda:next(states)
            worker.cleanup_owned_process(p,primary)
        self.assertTrue(getattr(primary,'worker_liveness_unknown',False))


if __name__=='__main__':unittest.main()

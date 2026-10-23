"""Trusted synchronous host boundary, isolated guard/state only, no real agent."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'tests/worker_acceptance')]
from invocation_guard import InvocationGuard
from code_worker import WorkerLivenessUnknown
import test_continuation_recovery as fixture

class HostBoundary(unittest.TestCase):
    def setUp(self):
        self.f=fixture.RecoveryAcceptance();self.f.setUp()
        self.guard=InvocationGuard(self.f.store,'boundary-run','/fixture',enabled=True)
        self.events=[];self.states=iter(['stopped','stopped']);self.saved=[]
    def tearDown(self):self.f.tearDown()
    def observe(self):self.events.append('observe');return next(self.states)
    def preserve(self,result,status):self.events.append('preserve');self.saved.append((result,status))
    def dispatch(self):self.events.append('dispatch');return {'owned':'result'}
    def call(self,dispatch=None):
        return self.guard.call_host(dispatch or self.dispatch,observe=self.observe,preserve=self.preserve)
    def test_new_boundary_contract_exists(self):
        self.assertTrue(callable(getattr(self.guard,'call_host',None)))
    def test_success_preserves_before_return_and_does_not_reserve_again(self):
        with self.guard:
            before=self.f.store.public_checkpoint()['run_count']
            self.assertEqual(self.call(),{'owned':'result'})
            self.assertEqual(self.f.store.public_checkpoint()['run_count'],before)
        self.assertEqual(self.events,['observe','dispatch','observe','preserve'])
        self.assertEqual(self.saved[0][1],{'outcome':'returned','liveness':'stopped'})
    def test_stop_before_dispatch_refuses(self):
        with self.guard:
            self.f.state.with_suffix('.stop').write_text('stop')
            with self.assertRaises(RuntimeError):self.call()
        self.assertEqual(self.events,[])
    def test_stop_after_dispatch_preserves_result_before_refusing(self):
        def dispatch():
            result=self.dispatch();self.f.state.with_suffix('.stop').write_text('stop');return result
        with self.guard,self.assertRaises(RuntimeError):self.call(dispatch)
        self.assertEqual(self.saved[0][0],{'owned':'result'})
    def test_deadline_after_dispatch_preserves_result(self):
        with patch('invocation_guard.time.monotonic',return_value=100) as clock:
            with self.guard:
                def dispatch():clock.return_value=1900;return self.dispatch()
                with self.assertRaises(TimeoutError):self.call(dispatch)
        self.assertEqual(len(self.saved),1)
    def test_unknown_before_dispatch_does_not_call(self):
        self.states=iter(['unknown'])
        with self.guard,self.assertRaises(WorkerLivenessUnknown):self.call()
        self.assertNotIn('dispatch',self.events)
    def test_running_after_dispatch_preserves_and_refuses(self):
        self.states=iter(['stopped','running'])
        with self.guard,self.assertRaises(WorkerLivenessUnknown):self.call()
        self.assertEqual(self.saved[0][1]['liveness'],'unknown')
    def test_observation_error_refuses_without_leaking_error(self):
        with self.guard:
            with patch.object(self,'observe',side_effect=OSError('private observer detail')):
                with self.assertRaises(WorkerLivenessUnknown) as cm:self.call()
        self.assertNotIn('private',str(cm.exception))
        self.assertNotIn('dispatch',self.events)
    def test_dispatch_exception_identity_and_partial_files_retained(self):
        error=RuntimeError('owned failure')
        artifact=self.f.root/'partial.txt'
        def dispatch():artifact.write_text('partial');raise error
        with self.guard:
            with self.assertRaises(RuntimeError) as cm:self.call(dispatch)
        self.assertIs(cm.exception,error);self.assertEqual(artifact.read_text(),'partial')
        self.assertEqual(self.saved[0][1],{'outcome':'raised','liveness':'stopped'})
    def test_preservation_failure_is_unknown_no_return(self):
        with self.guard,patch.object(self,'preserve',side_effect=OSError('owned disk full')):
            with self.assertRaises(WorkerLivenessUnknown):self.call()
    def test_callbacks_required_and_inactive_guard_refuses(self):
        with self.assertRaises(ValueError):self.call()
        with self.guard:
            for key in ('observe','preserve'):
                args={'observe':self.observe,'preserve':self.preserve};args[key]=None
                with self.subTest(key=key),self.assertRaises(ValueError):
                    self.guard.call_host(self.dispatch,**args)
        self.assertNotIn('dispatch',self.events)

if __name__=='__main__':unittest.main()

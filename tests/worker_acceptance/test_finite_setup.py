import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('setup_under_test',ROOT/'scripts/code_worker.py');w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
class FiniteSetup(unittest.TestCase):
 def test_nonfinite_wait_rejected_before_os_lock(self):
  for seconds in [float('nan'),float('inf'),-float('inf')]:
   with self.subTest(seconds=seconds),tempfile.TemporaryDirectory() as d:
    p=Path(d)/'owned.sqlite'
    with self.assertRaises(ValueError):
     with w.setup_lock(p,seconds=seconds):pass
    self.assertEqual(list(Path(d).iterdir()),[])
 def test_contention_nonfinite_never_enters_wait_watchdog(self):
  for seconds in [float('nan'),float('inf')]:
   with self.subTest(seconds=seconds),tempfile.TemporaryDirectory() as d:
    with patch.object(w.fcntl,'flock',side_effect=BlockingIOError),patch.object(w.time,'monotonic',side_effect=[0,1e6,2e6,3e6]),patch.object(w.time,'sleep',side_effect=RuntimeError('owned watchdog')):
     try:
      with w.setup_lock(Path(d)/'owned.sqlite',seconds=seconds):pass
     except Exception as e:self.assertIsInstance(e,ValueError)
     else:self.fail('invalid timeout was accepted')
 def test_zero_and_negative_finite_keep_try_once(self):
  for seconds in [0,-1]:
   with tempfile.TemporaryDirectory() as d,patch.object(w.fcntl,'flock',side_effect=BlockingIOError),patch.object(w.time,'monotonic',return_value=10):
    with self.assertRaisesRegex(RuntimeError,'lock timeout'):
     with w.setup_lock(Path(d)/'owned.sqlite',seconds=seconds):pass
 def test_finite_uncontended_values_still_acquire_and_release(self):
  for seconds in [0,-1,.01,30]:
   with tempfile.TemporaryDirectory() as d:
    with w.setup_lock(Path(d)/'owned.sqlite',seconds=seconds):pass

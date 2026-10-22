"""Owned temporary lease state only; no retained controller state."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('lease_under_test',ROOT/'scripts/code_worker.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
class FiniteLease(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.l=w.Leases(Path(self.tmp.name)/'owned.sqlite')
 def tearDown(self):self.l.close();self.tmp.cleanup()
 def test_rejects_nonfinite_duration_without_writing(self):
  for x in [float('nan'),float('inf'),-float('inf')]:
   with self.subTest(x=x),self.assertRaises(ValueError):self.l.claim({'id':'invalid','lane':'A'},seconds=x,now=100)
  self.assertEqual(self.l.report(),[])
 def test_rejects_nonpositive_duration_without_writing(self):
  for x in [0,-1]:
   with self.subTest(x=x),self.assertRaises(ValueError):self.l.claim({'id':'invalid','lane':'A'},seconds=x,now=100)
  self.assertEqual(self.l.report(),[])
 def test_rejects_boolean_and_text_duration(self):
  for x in [True,False,'30']:
   with self.subTest(x=x),self.assertRaises(ValueError):self.l.claim({'id':'invalid','lane':'A'},seconds=x,now=100)
  self.assertEqual(self.l.report(),[])
 def test_invalid_clock_preserves_existing_lease(self):
  token=self.l.claim({'id':'existing','lane':'A'},seconds=30,now=100)
  for x in [float('nan'),float('inf'),-float('inf'),True,'100']:
   with self.subTest(x=x),self.assertRaises(ValueError):self.l.claim({'id':'other','lane':'B'},now=x)
  self.assertEqual([(r['id'],r['status']) for r in self.l.report()],[('existing','running')])
  self.l.finish('existing',token,'implemented',{},now=101)
 def test_rejects_overflowing_expiry(self):
  with self.assertRaises(ValueError):self.l.claim({'id':'invalid','lane':'A'},seconds=1e308,now=1e308)
  self.assertEqual(self.l.report(),[])
 def test_valid_fractional_duration_and_epoch_clock(self):
  t={'id':'valid','lane':'A'};token=self.l.claim(t,seconds=.5,now=0)
  self.l.finish(t['id'],token,'implemented',{},now=.25)
  self.assertEqual(self.l.report()[0]['status'],'implemented')
 def test_valid_duration_still_expires_without_takeover(self):
  t={'id':'valid','lane':'A'};self.l.claim(t,seconds=2,now=10)
  self.assertIsNone(self.l.claim(t,now=12));self.assertEqual(self.l.report()[0]['status'],'blocked')

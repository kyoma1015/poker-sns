"""Explicit partial mode must be bool, not arbitrary false-like input."""
import unittest
from gto.hand169 import aggregate
class CoverageFlag(unittest.TestCase):
 def test_nonboolean_flags_rejected(self):
  for flag in [None,0,1,'', 'false',[],{},()]:
   with self.subTest(flag=flag),self.assertRaises(ValueError):aggregate([],1,require_complete=flag)
 def test_invalid_flag_does_not_iterate_input(self):
  class Untouched:
   def __iter__(self):raise AssertionError('invalid mode consumed records')
  with self.assertRaises(ValueError):aggregate(Untouched(),1,require_complete=None)
 def test_explicit_partial_retained(self):
  r=aggregate([],1,require_complete=False);self.assertFalse(r['complete']);self.assertEqual(r['concrete_combinations'],0)
 def test_default_and_true_reject_incomplete(self):
  with self.assertRaises(ValueError):aggregate([],1)
  with self.assertRaises(ValueError):aggregate([],1,require_complete=True)

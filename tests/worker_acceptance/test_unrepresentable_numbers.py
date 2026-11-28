"""Reject numbers outside the export's finite binary64 input domain."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gto.hand169 import aggregate


class FiniteNumberValidation(unittest.TestCase):
    def row(self):
        return {'cards': ['As', 'Ks'], 'weight': 2, 'frequencies': [1], 'ev': -4}

    def reject(self, field, value):
        row = self.row()
        row[field] = [value] if field == 'frequencies' else value
        with self.assertRaises(ValueError):
            aggregate([row], 1, require_complete=False)

    def test_positive_huge_weight(self): self.reject('weight', 10**400)
    def test_negative_huge_weight(self): self.reject('weight', -(10**400))
    def test_positive_huge_ev(self): self.reject('ev', 10**400)
    def test_negative_huge_ev(self): self.reject('ev', -(10**400))
    def test_positive_huge_frequency(self): self.reject('frequencies', 10**400)
    def test_negative_huge_frequency(self): self.reject('frequencies', -(10**400))

    def test_existing_invalid_numbers(self):
        for field in ('weight', 'frequencies', 'ev'):
            for value in (float('inf'), float('-inf'), float('nan'), True, '1'):
                with self.subTest(field=field, value=repr(value)):
                    self.reject(field, value)

    def test_ordinary_integer_input_preserved(self):
        result = aggregate([self.row()], 1, require_complete=False)['hands']['AKs']
        self.assertEqual(result['reach_mass'], 2)
        self.assertEqual(result['frequencies'], [1])
        self.assertEqual(result['ev'], -4)

"""Finite mean must not be lost to rounded-term fsum overflow."""
from fractions import Fraction
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gto.hand169 import aggregate


class WeightedMaximum(unittest.TestCase):
    def check(self, weight, value):
        rows = [{'cards': cards, 'weight': weight, 'frequencies': [1.0], 'ev': value}
                for cards in (['As', 'Ks'], ['Ah', 'Kh'], ['Ad', 'Kd'])]
        mass = math.fsum(row['weight'] for row in rows)
        expected = float(sum((Fraction(row['weight']) * Fraction(row['ev'])
                              for row in rows), Fraction(0)) / Fraction(mass))
        self.assertEqual(expected, value)
        result = aggregate(rows, 1, require_complete=False)['hands']['AKs']
        self.assertEqual(result['ev'], expected)
        self.assertEqual(result['reach_mass'], mass)
        self.assertEqual(result['frequencies'], [1.0])

    def test_positive_maximum_normal_weight(self): self.check(1.0, sys.float_info.max)
    def test_negative_maximum_normal_weight(self): self.check(1.0, -sys.float_info.max)
    def test_positive_maximum_subnormal_weight(self): self.check(5e-324, sys.float_info.max)
    def test_negative_maximum_subnormal_weight(self): self.check(5e-324, -sys.float_info.max)

"""Immutable hand-derived seven-card expectations; not G11 strategy baselines."""
import unittest
from gto.native.settlement import reference_module, run_rank7_case, validate_rank7_cards


def cards(text):
    ranks = '23456789TJQKA'; suits = 'cdhs'
    return [ranks.index(c[0]) * 4 + suits.index(c[1]) for c in text.split()]


CASES = [
    ('high_card', 'Ac Kd 9h 7s 5c 3d 2h', [0, 14, 13, 9, 7, 5]),
    ('one_pair', 'Ac Ad Kh 9s 7c 4d 2h', [1, 14, 13, 9, 7]),
    ('two_pair', 'Ac Ad Kh Ks 9c 4d 2h', [2, 14, 13, 9]),
    ('trips', 'Ac Ad Ah Ks 9c 4d 2h', [3, 14, 13, 9]),
    ('straight', '9c Td Jh Qs Kc 3d 2h', [4, 13]),
    ('wheel', 'Ac 2d 3h 4s 5c 9d Th', [4, 5]),
    ('flush', 'Ac Jc 9c 7c 3c Kd Qh', [5, 14, 11, 9, 7, 3]),
    ('full_house', 'Ac Ad Ah Ks Kc 4d 2h', [6, 14, 13]),
    ('two_trips', 'Ac Ad Ah Ks Kc Kd 2h', [6, 14, 13]),
    ('quads', 'Ac Ad Ah As Kc 4d 2h', [7, 14, 13]),
    ('straight_flush', '9c Tc Jc Qc Kc 3d 2h', [8, 13]),
    ('wheel_straight_flush', 'Ac 2c 3c 4c 5c Kd Qh', [8, 5]),
]


class Rank7Acceptance(unittest.TestCase):
    def test_hand_derived_nine_categories_and_wheels(self):
        with reference_module() as ref:
            for name, encoded, expected in CASES:
                with self.subTest(name=name):
                    result = run_rank7_case(ref, {'id': name, 'cards': cards(encoded), 'expected': expected})
                    self.assertEqual(result['rank'], expected)
                    self.assertFalse(result['native_compared'])

    def test_rejects_bad_cards_before_native_call(self):
        class NeverCalled:
            def rank7(self, values):
                raise AssertionError('invalid input reached native boundary')
        invalid = [list(range(6)), list(range(8)), [0, 0, 2, 3, 4, 5, 6],
                   [-1, 1, 2, 3, 4, 5, 6], [0, 1, 2, 3, 4, 5, 52],
                   [False, 1, 2, 3, 4, 5, 6], [0.0, 1, 2, 3, 4, 5, 6],
                   ['0', 1, 2, 3, 4, 5, 6], None]
        with reference_module() as ref:
            for values in invalid:
                with self.subTest(values=values), self.assertRaises(ValueError):
                    run_rank7_case(ref, {'id': 'bad', 'cards': values, 'expected': [0]}, NeverCalled())

    def test_board_playing_tie_and_pair_kickers(self):
        with reference_module() as ref:
            def rank(encoded, expected):
                return run_rank7_case(ref, {'id':'tie', 'cards':cards(encoded), 'expected':expected})['rank']
            a = rank('Ac Kc Qc Jc Tc 2d 3h', [8,14])
            b = rank('Ac Kc Qc Jc Tc 4d 5h', [8,14])
            self.assertEqual(a,b)
            self.assertGreater(rank('Ac Ad Kh Qs 9c 4d 2h', [1,14,13,12,9]),
                               rank('Ac Ad Kh Js 9c 4d 2h', [1,14,13,11,9]))

    def test_invalid_expected_rank_is_not_a_pass(self):
        with reference_module() as ref, self.assertRaises(AssertionError):
            run_rank7_case(ref, {'id':'wrong', 'cards':cards(CASES[0][1]), 'expected':[8,14]})

if __name__ == '__main__': unittest.main()

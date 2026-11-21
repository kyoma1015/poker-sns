"""Dependency-free joint range boundaries; no native runtime required."""
from fractions import Fraction as F
import unittest
from gto.native.joint_support import condition_joint_support,product_support


class JointSupportBoundaries(unittest.TestCase):
    def test_entire_product_can_be_removed_without_inventing_posterior(self):
        ranges={1:[([0,1],F(1))],2:[([1,2],F(1))]}
        result=product_support(3,[48,49],ranges)
        self.assertEqual(result['deals'],[])
        self.assertEqual(result['compatible_prior_mass'],0)
        self.assertEqual(result['removed_prior_mass'],1)
        self.assertFalse(result['support_complete'])

    def test_seat_swaps_remain_distinct_but_exact_duplicates_fail(self):
        deals=[([[0,1],[2,3]],F(1,2)),([[2,3],[0,1]],F(1,2))]
        result=condition_joint_support(3,[48,49],deals)
        self.assertEqual(result['positive_compatible_deals'],2)
        self.assertNotEqual(result['deals'][0][0],result['deals'][1][0])

    def test_zero_mass_rows_do_not_inflate_positive_coverage(self):
        result=condition_joint_support(2,[48,49],[([[0,1]],F(1)),([[1,0]],F(0))])
        self.assertEqual(result['positive_compatible_deals'],1)
        self.assertEqual(result['uniform_ordered_support_fraction'],F(1,2450))

    def test_public_board_changes_available_ordered_support_count(self):
        result=condition_joint_support(2,[48,49],[([[0,1]],F(1))],[4,8,12])
        self.assertEqual(result['full_ordered_opponent_deals'],str(47*46))
        self.assertEqual(result['uniform_ordered_support_fraction'],F(1,47*46))

    def test_invalid_card_domains_and_control_types_fail(self):
        for hand in ([True,1],[-1,1],[0,52],[0,0]):
            with self.subTest(hand=hand),self.assertRaises(ValueError):
                condition_joint_support(2,[48,49],[([hand],F(1))])
        for kwargs in ({'hero_seat':True},{'hero_seat':2},{'max_deals':True},{'max_deals':0}):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                condition_joint_support(2,[48,49],[([[0,1]],F(1))],**kwargs)

    def test_product_ranges_require_exact_normalization_and_all_seats(self):
        for ranges in ({1:[([0,1],F(1,2))]}, {1:[([0,1],1.0)]},
                       {1:[([0,1],F(-1)),([2,3],F(2))]}, {},
                       {True:[([0,1],F(1))]}):
            with self.subTest(ranges=ranges),self.assertRaises(ValueError):
                product_support(2,[48,49],ranges)


if __name__=='__main__':unittest.main()

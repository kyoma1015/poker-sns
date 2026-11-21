from fractions import Fraction as F
import unittest
from gto.native.deviation import local_deviation
from gto.native.infoset_export import PolicySnapshot,UnknownPolicyRow


def estimate(value):
    return {'sample_mean_values':[F(-value,2),F(-value,2),F(value)],
            'simultaneous_chip_intervals':[[-value/2,-value/2],[-value/2,-value/2],[value,value]]}


class Deviation(unittest.TestCase):
    def test_multiway_local_gain_is_not_divided_by_two_or_called_exploitability(self):
        r=local_deviation({0:F(1,2),1:F(1,2)},{0:estimate(0),1:estimate(4)},[0,1],2)
        self.assertEqual(r['estimated_restricted_gain'],2)
        self.assertAlmostEqual(r['full_local_gain_upper_bound'],2)
        self.assertIsNone(r['global_exploitability']);self.assertIsNone(r['nash_conv'])
        self.assertFalse(r['convergence_verified'])

    def test_omitted_legal_action_prevents_full_local_upper_bound(self):
        r=local_deviation({0:F(1),1:F(0),2:F(0)},{0:estimate(0),1:estimate(3)},[0,1,2],2)
        self.assertEqual(r['estimated_restricted_gain'],3)
        self.assertIsNone(r['full_local_gain_upper_bound'])
        self.assertFalse(r['all_legal_actions_evaluated'])

    def test_missing_positive_profile_action_prevents_gain_estimate(self):
        r=local_deviation({0:F(1,2),1:F(1,2)},{0:estimate(0),1:None},[0,1],2)
        self.assertEqual(r['status'],'profile_action_values_missing')
        self.assertNotIn('estimated_restricted_gain',r)

    def test_unknown_target_policy_is_not_uniform(self):
        r=local_deviation(None,{0:estimate(0)},[0,1],2)
        self.assertEqual(r['status'],'target_policy_unobserved')

    def test_bad_profile_and_intervals_rejected(self):
        with self.assertRaises(ValueError):local_deviation({0:F(1,2)},{0:estimate(0)},[0],2)
        row=estimate(2);row['simultaneous_chip_intervals'][2]=[3,1]
        with self.assertRaises(ValueError):local_deviation({0:F(1)},{0:row},[0],2)

    def test_missing_snapshot_row_distinct_from_wrong_action_identity(self):
        class State:
            def is_terminal(self):return False
            def is_chance_node(self):return False
            def current_player(self):return 0
            def information_state_string(self,player):return 'observed'
            def legal_actions(self):return [0,1]
        node=State();missing=PolicySnapshot({'other':{0:F(1)}})
        self.assertIsNone(missing.observed_row(node))
        with self.assertRaises(UnknownPolicyRow):missing(node)
        wrong=PolicySnapshot({'observed':{0:F(1)}})
        with self.assertRaisesRegex(ValueError,'actions differ'):wrong.observed_row(node)


if __name__=='__main__':unittest.main()

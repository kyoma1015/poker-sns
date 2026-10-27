"""Statistical/action-bound math only; synthetic counts never enter UI catalog."""
from fractions import Fraction
import json
import unittest
from gto.hand169 import CLASSES,hand_class
from gto.native.hand169_bridge import card_name
from gto.native.onebb_certificate import evaluate_counts,native_profile_bound,representative


def counts():
    return {label:{'wins':4500,'losses':4500,'ties':1000,'samples':10000,'seed':17} for label in CLASSES}


class OneBBMath(unittest.TestCase):
    def test_all_canonical_cards_match_their169class(self):
        for label in CLASSES:self.assertEqual(hand_class([card_name(c) for c in representative(label)]),label)

    def test_simultaneous_dominance_bounds_every_infoset_of_this_game(self):
        result=evaluate_counts(counts())
        self.assertTrue(result['all_classes_call_dominant'])
        self.assertEqual(result['max_unilateral_gain_upper_bb'],0)
        self.assertEqual(result['strategic_infosets'],2652)
        self.assertEqual(sum(row['combinations'] for row in result['hands'].values()),1326)
        self.assertAlmostEqual(result['hands']['AA']['evBb'],0)

    def test_sampling_uncertainty_can_prevent_certification(self):
        data=counts();data['32o'].update(wins=2000,losses=7000,ties=1000)
        result=evaluate_counts(data)
        self.assertFalse(result['all_classes_call_dominant'])
        self.assertGreater(result['max_unilateral_gain_upper_bb'],0)

    def test_missing_or_modified_sample_counts_rejected(self):
        for change in (lambda d:d.pop('AA'),lambda d:d['AA'].update(samples=9999),
                       lambda d:d['AA'].update(wins=True)):
            data=counts();change(data)
            with self.assertRaises(ValueError):evaluate_counts(data)

    def test_root_prior_symmetry_check_is_not_ignored(self):
        data=counts()
        for row in data.values():row.update(wins=10000,losses=0,ties=0)
        with self.assertRaisesRegex(ValueError,'ex-ante'):evaluate_counts(data)

    def test_initializer_pseudocount_is_not_an_updated_policy(self):
        class Solver:
            iteration=1
            def keys(self):return [json.dumps({'seat':0,'board':[],'betting_history':[],'hand':[48,49]})]
            def row(self,key):return {'updates':0,'actions':[0,1],'average':[1e-6,1e-6]}
        result=native_profile_bound(Solver(),counts())
        self.assertEqual(result['updated_ordered_infosets'],0)
        self.assertFalse(result['complete_policy_coverage'])
        self.assertGreater(result['full_game_unilateral_gain_interval_bb'][1],0)

    def test_updated_native_rows_keep_missing_information_sets_conservative(self):
        class Solver:
            iteration=1
            def keys(self):return [json.dumps({'seat':0,'board':[],'betting_history':[],'hand':[48,49]})]
            def row(self,key):return {'updates':1,'actions':[0,1],'average':[0.0,1.0]}
        result=native_profile_bound(Solver(),counts())
        self.assertEqual(result['updated_ordered_infosets'],1)
        self.assertGreater(result['full_game_unilateral_gain_interval_bb'][1],0)


if __name__=='__main__':unittest.main()

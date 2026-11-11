from collections import Counter
from itertools import combinations
import unittest
from gto.hand169 import aggregate, CLASSES, DECK, hand_class


class Hand169(unittest.TestCase):
    def record(self, cards, weight=1., frequencies=None, ev=2.):
        return {'cards':cards,'weight':weight,'frequencies':[.25,.75] if frequencies is None else frequencies,'ev':ev}
    def test_complete_deck_counts(self):
        counts=Counter(hand_class(pair) for pair in combinations(DECK,2))
        self.assertEqual(len(CLASSES),169);self.assertEqual(len(set(CLASSES)),169)
        self.assertEqual(set(counts),set(CLASSES));self.assertEqual(sum(counts.values()),1326)
        for label,count in counts.items():self.assertEqual(count,6 if len(label)==2 else 4 if label.endswith('s') else 12)
    def test_order_and_suit_invariance(self):
        self.assertEqual(hand_class(['As','Kh']),hand_class(['Kh','As']))
        self.assertEqual(hand_class(['Ah','Kd']),'AKo')
        self.assertEqual(hand_class(['Kh','Ah']),'AKs')
    def test_invalid_cards(self):
        for cards in (['As','As'],['As'],['Xs','Ah'],['as','Kh'],['AS','Kh']):
            with self.assertRaises(ValueError):hand_class(cards)
    def test_complete_export_conserves_mass_policy_and_ev(self):
        result=aggregate((self.record(list(pair)) for pair in combinations(DECK,2)),2)
        self.assertTrue(result['complete']);self.assertEqual(result['concrete_combinations'],1326)
        self.assertEqual(sum(x['reach_mass'] for x in result['hands'].values()),1326)
        for row in result['hands'].values():
            self.assertAlmostEqual(row['frequencies'][0],.25);self.assertAlmostEqual(row['frequencies'][1],.75);self.assertAlmostEqual(row['ev'],2.)
    def test_partial_coverage_is_explicit_and_rejected_by_default(self):
        rows=[self.record(['As','Kh'])]
        with self.assertRaisesRegex(ValueError,'coverage'):aggregate(rows,2)
        result=aggregate(rows,2,require_complete=False)
        self.assertFalse(result['complete']);self.assertIsNone(result['hands']['AA']['frequencies'])
    def test_weighted_mean_not_unweighted_mean(self):
        rows=[self.record(['As','Kh'],1,[1,0],2),self.record(['Ah','Kd'],3,[0,1],6)]
        result=aggregate(rows,2,require_complete=False)['hands']['AKo']
        self.assertEqual(result['frequencies'],[.25,.75]);self.assertEqual(result['ev'],5.)
    def test_zero_mass_and_unknown_ev_stay_unknown(self):
        row=aggregate([self.record(['As','Ah'],0)],2,require_complete=False)['hands']['AA']
        self.assertIsNone(row['frequencies']);self.assertIsNone(row['ev'])
        row=aggregate([self.record(['As','Ah'],ev=None)],2,require_complete=False)['hands']['AA']
        self.assertIsNone(row['ev'])
    def test_duplicate_combination_rejected_even_reversed(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):aggregate([self.record(['As','Kh']),self.record(['Kh','As'])],2,require_complete=False)
    def test_invalid_numeric_inputs(self):
        for key,value in [('weight',-1),('weight',float('nan')),('weight',True),('ev',float('inf')),('frequencies',[.5,.6]),('frequencies',[-.1,1.1]),('frequencies',[True,False]),('frequencies',[1.])]:
            row=self.record(['As','Kh']);row[key]=value
            with self.subTest(key=key,value=value):
                with self.assertRaises(ValueError):aggregate([row],2,require_complete=False)
    def test_large_finite_ev_avoids_multiplication_overflow(self):
        rows=[self.record(['As','Kh'],1e200,[1,0],1e200),self.record(['Ah','Kd'],1e200,[0,1],1e200)]
        self.assertEqual(aggregate(rows,2,require_complete=False)['hands']['AKo']['ev'],1e200)

if __name__=='__main__':unittest.main()

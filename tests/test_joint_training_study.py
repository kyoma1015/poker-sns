import unittest
from gto.abstract import joint_training_study as study

class TrainingStudyTests(unittest.TestCase):
    def test_registered_gate_rejects_damping_and_mixture(self):
        result=study.run()
        self.assertEqual(result['eligible_candidates'],['delayed_output33'])
        self.assertEqual(result['formal_acceptance'],[0,12])
        for game in result['games']:
            self.assertLess(game['candidates']['delayed_output33']['points'][-1]['nc'],game['candidates']['full_history']['points'][-1]['nc']*.9)
            for candidate in game['candidates'].values():self.assertTrue(candidate['history_retained'])

if __name__=='__main__':unittest.main()

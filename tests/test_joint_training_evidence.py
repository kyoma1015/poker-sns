import unittest
from gto.abstract import joint_training_evidence as evidence

class EvidenceTests(unittest.TestCase):
    def test_mismatched_checkpoint_cannot_claim_average_support(self):
        class DifferentPolicy:
            def meta(self):return {'epoch':7}
            def digest(self):return 'actual'
        with self.assertRaisesRegex(ValueError,'checkpoint differ'):evidence.export({'epoch':7,'state_digest':'other'},DifferentPolicy())
if __name__=='__main__':unittest.main()

import unittest
from gto.abstract.joint_update_report import checked,improves
class EvidenceGuard(unittest.TestCase):
    def valid(self):return {'coverage':1,'evaluated_orbits':1755,'population_orbits':1755,'restricted_nashconv_interval_bb':[.09,.09],'sb_br_gain_bb':.04,'bb_br_gain_bb':.05,'partial_sb_ev_bb':.1,'full_real_game_gto_verified':False,'formal_acceptance':0}
    def test_restricted_success_never_admits_real_gto(self):
        r=checked(self.valid());self.assertTrue(r['restricted_target_pass']);self.assertFalse(r['ordinary_admission'])
    def test_incomplete_or_misnormalized_or_nonfinite_evidence_rejected(self):
        for patch in [{'coverage':.99},{'population_orbits':28},{'sb_br_gain_bb':-.01},{'bb_br_gain_bb':.1},{'partial_sb_ev_bb':float('nan')},{'formal_acceptance':1},{'full_real_game_gto_verified':True}]:
            with self.subTest(patch=patch),self.assertRaises(ValueError):checked({**self.valid(),**patch})
    def test_roundoff_is_not_a_quality_improvement(self):
        self.assertFalse(improves(.932107152722077,.9321071527220774));self.assertTrue(improves(.8,.9321071527220774))
    def test_worse_than_target_is_recorded_as_failure(self):
        r=checked({**self.valid(),'restricted_nashconv_interval_bb':[1.2,1.2],'sb_br_gain_bb':.6,'bb_br_gain_bb':.6});self.assertFalse(r['restricted_target_pass'])
if __name__=='__main__':unittest.main()
